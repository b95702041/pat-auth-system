"""CLI management tool for Personal Access Token system."""
import typer
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from rich.console import Console
from rich.table import Table

from app.database import SessionLocal
from app.models.user import User
from app.models.token import Token
from app.schemas.token import TokenCreate
from app.services.token_service import TokenService

app = typer.Typer(help="Personal Access Token Management CLI")
users_app = typer.Typer(help="User management commands")
tokens_app = typer.Typer(help="Token management commands")
app.add_typer(users_app, name="users")
app.add_typer(tokens_app, name="tokens")

console = Console()


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here, will close after command


@users_app.command("list")
def list_users():
    """List all users."""
    db = get_db()
    try:
        users = db.query(User).all()
        
        if not users:
            console.print("[yellow]No users found.[/yellow]")
            return
        
        table = Table(title="Users")
        table.add_column("ID", style="cyan")
        table.add_column("Username", style="green")
        table.add_column("Email", style="blue")
        table.add_column("Active", style="magenta")
        table.add_column("Created At", style="yellow")
        
        for user in users:
            table.add_row(
                user.id,
                user.username,
                user.email,
                "✓" if user.is_active else "✗",
                user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "N/A"
            )
        
        console.print(table)
        console.print(f"\n[bold]Total users:[/bold] {len(users)}")
    finally:
        db.close()


@tokens_app.command("list")
def list_tokens(
    user_id: str = typer.Option(None, "--user-id", "-u", help="Filter by user ID"),
    show_all: bool = typer.Option(False, "--all", "-a", help="Show all tokens including revoked")
):
    """List tokens."""
    db = get_db()
    try:
        query = db.query(Token)
        
        if user_id:
            query = query.filter(Token.user_id == user_id)
        
        if not show_all:
            query = query.filter(Token.is_revoked == False)
        
        tokens = query.all()
        
        if not tokens:
            console.print("[yellow]No tokens found.[/yellow]")
            return
        
        table = Table(title=f"Tokens{' (All)' if show_all else ' (Active)'}")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("User ID", style="blue", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Prefix", style="magenta")
        table.add_column("Scopes", style="yellow")
        table.add_column("Status", style="white")
        table.add_column("Expires At", style="red")
        
        for token in tokens:
            # Determine status
            if token.is_revoked:
                status = "[red]Revoked[/red]"
            elif token.expires_at < datetime.utcnow():
                status = "[yellow]Expired[/yellow]"
            else:
                status = "[green]Active[/green]"
            
            table.add_row(
                token.id[:8] + "...",
                token.user_id[:8] + "...",
                token.name,
                token.token_prefix,
                ", ".join(token.scopes[:2]) + ("..." if len(token.scopes) > 2 else ""),
                status,
                token.expires_at.strftime("%Y-%m-%d")
            )
        
        console.print(table)
        console.print(f"\n[bold]Total tokens:[/bold] {len(tokens)}")
    finally:
        db.close()


@tokens_app.command("revoke")
def revoke_token(
    token_id: str = typer.Argument(..., help="Token ID to revoke")
):
    """Revoke a token."""
    db = get_db()
    try:
        token = db.query(Token).filter(Token.id == token_id).first()
        
        if not token:
            console.print(f"[red]Error: Token '{token_id}' not found.[/red]")
            raise typer.Exit(1)
        
        if token.is_revoked:
            console.print(f"[yellow]Token '{token.name}' is already revoked.[/yellow]")
            return
        
        token.is_revoked = True
        db.commit()
        
        console.print(f"[green]✓ Token '{token.name}' has been revoked.[/green]")
    finally:
        db.close()


@tokens_app.command("create")
def create_token(
    user_id: str = typer.Option(..., "--user-id", "-u", help="User ID"),
    name: str = typer.Option(..., "--name", "-n", help="Token name"),
    scopes: str = typer.Option(..., "--scopes", "-s", help="Comma-separated scopes"),
    days: int = typer.Option(90, "--days", "-d", help="Expiration days")
):
    """Create a new token (admin use)."""
    db = get_db()
    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            console.print(f"[red]Error: User '{user_id}' not found.[/red]")
            raise typer.Exit(1)
        
        # Parse scopes
        scope_list = [s.strip() for s in scopes.split(",")]
        
        # Create token
        token_data = TokenCreate(
            name=name,
            scopes=scope_list,
            expires_in_days=days
        )
        
        token, full_token = TokenService.create_token(db, user_id, token_data)
        
        console.print(f"\n[green]✓ Token created successfully![/green]\n")
        console.print(f"[bold]Token ID:[/bold] {token.id}")
        console.print(f"[bold]Token Name:[/bold] {token.name}")
        console.print(f"[bold]User:[/bold] {user.username} ({user.email})")
        console.print(f"[bold]Scopes:[/bold] {', '.join(token.scopes)}")
        console.print(f"[bold]Expires:[/bold] {token.expires_at.strftime('%Y-%m-%d %H:%M')}")
        console.print(f"\n[yellow]Full Token (save this, it won't be shown again):[/yellow]")
        console.print(f"[cyan]{full_token}[/cyan]\n")
    finally:
        db.close()


@app.command("stats")
def show_stats():
    """Show token statistics."""
    db = get_db()
    try:
        total_users = db.query(User).count()
        total_tokens = db.query(Token).count()
        active_tokens = db.query(Token).filter(
            Token.is_revoked == False,
            Token.expires_at > datetime.utcnow()
        ).count()
        revoked_tokens = db.query(Token).filter(Token.is_revoked == True).count()
        expired_tokens = db.query(Token).filter(
            Token.is_revoked == False,
            Token.expires_at <= datetime.utcnow()
        ).count()
        
        console.print("\n[bold cyan]Token System Statistics[/bold cyan]\n")
        console.print(f"[bold]Total Users:[/bold] {total_users}")
        console.print(f"[bold]Total Tokens:[/bold] {total_tokens}")
        console.print(f"[bold green]Active Tokens:[/bold green] {active_tokens}")
        console.print(f"[bold red]Revoked Tokens:[/bold red] {revoked_tokens}")
        console.print(f"[bold yellow]Expired Tokens:[/bold yellow] {expired_tokens}")
        console.print()
    finally:
        db.close()


@tokens_app.command("cleanup")
def cleanup_tokens(
    days: int = typer.Option(30, "--days", "-d", help="Delete tokens expired more than N days ago"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be deleted without deleting")
):
    """Clean up expired tokens."""
    db = get_db()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        tokens_to_delete = db.query(Token).filter(
            Token.expires_at < cutoff_date
        ).all()
        
        if not tokens_to_delete:
            console.print(f"[green]No tokens to clean up (expired more than {days} days ago).[/green]")
            return
        
        console.print(f"\n[yellow]Found {len(tokens_to_delete)} token(s) to delete:[/yellow]\n")
        
        for token in tokens_to_delete:
            days_expired = (datetime.utcnow() - token.expires_at).days
            console.print(f"  • {token.name} (expired {days_expired} days ago)")
        
        if dry_run:
            console.print(f"\n[cyan]Dry run - no tokens were deleted.[/cyan]")
            return
        
        # Confirm deletion
        confirm = typer.confirm(f"\nDelete {len(tokens_to_delete)} token(s)?")
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            return
        
        # Delete tokens
        for token in tokens_to_delete:
            db.delete(token)
        
        db.commit()
        console.print(f"\n[green]✓ Deleted {len(tokens_to_delete)} token(s).[/green]")
    finally:
        db.close()


@tokens_app.command("info")
def token_info(
    token_id: str = typer.Argument(..., help="Token ID")
):
    """Show detailed information about a token."""
    db = get_db()
    try:
        token = db.query(Token).filter(Token.id == token_id).first()
        
        if not token:
            console.print(f"[red]Error: Token '{token_id}' not found.[/red]")
            raise typer.Exit(1)
        
        user = db.query(User).filter(User.id == token.user_id).first()
        
        # Determine status
        if token.is_revoked:
            status = "[red]Revoked[/red]"
        elif token.expires_at < datetime.utcnow():
            status = "[yellow]Expired[/yellow]"
        else:
            status = "[green]Active[/green]"
        
        console.print(f"\n[bold cyan]Token Information[/bold cyan]\n")
        console.print(f"[bold]ID:[/bold] {token.id}")
        console.print(f"[bold]Name:[/bold] {token.name}")
        console.print(f"[bold]Prefix:[/bold] {token.token_prefix}")
        console.print(f"[bold]User:[/bold] {user.username if user else 'Unknown'} ({token.user_id})")
        console.print(f"[bold]Scopes:[/bold] {', '.join(token.scopes)}")
        console.print(f"[bold]Status:[/bold] {status}")
        console.print(f"[bold]Created:[/bold] {token.created_at.strftime('%Y-%m-%d %H:%M:%S') if token.created_at else 'N/A'}")
        console.print(f"[bold]Expires:[/bold] {token.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"[bold]Last Used:[/bold] {token.last_used_at.strftime('%Y-%m-%d %H:%M:%S') if token.last_used_at else 'Never'}")
        
        if token.allowed_ips:
            console.print(f"[bold]Allowed IPs:[/bold] {', '.join(token.allowed_ips)}")
        else:
            console.print(f"[bold]Allowed IPs:[/bold] Any")
        
        console.print()
    finally:
        db.close()


if __name__ == "__main__":
    app()