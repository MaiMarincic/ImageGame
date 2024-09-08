import sqlite3
import click

DB_NAME = 'game_database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.commit()
    conn.close()

@click.group()
def cli():
    """CLI application to view the game database."""
    init_db()

@cli.command()
def users():
    """View all users."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()
    conn.close()
    
    click.echo("Users:")
    for user in users:
        click.echo(f"ID: {user[0]}, Name: {user[1]}")

@cli.command()
def games():
    """View all games."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT Game.Id, Users.Name
    FROM Game
    LEFT JOIN Users ON Game.Winner_Id = Users.Id
    """)
    games = cursor.fetchall()
    conn.close()
    
    click.echo("Games:")
    for game in games:
        winner = game[1] if game[1] else "No winner yet"
        click.echo(f"Game ID: {game[0]}, Winner: {winner}")

@cli.command()
@click.argument('game_id', type=int)
def game_details(game_id):
    """View details of a specific game."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Get game info
    cursor.execute("""
    SELECT Game.Id, Users.Name
    FROM Game
    LEFT JOIN Users ON Game.Winner_Id = Users.Id
    WHERE Game.Id = ?
    """, (game_id,))
    game = cursor.fetchone()
    
    if not game:
        click.echo(f"No game found with ID {game_id}")
        return
    
    winner = game[1] if game[1] else "No winner yet"
    click.echo(f"Game ID: {game[0]}, Winner: {winner}")
    
    # Get participants
    cursor.execute("""
    SELECT Users.Name
    FROM GameParticipants
    JOIN Users ON GameParticipants.User_Id = Users.Id
    WHERE GameParticipants.Game_Id = ?
    """, (game_id,))
    participants = cursor.fetchall()
    
    click.echo("Participants:")
    for participant in participants:
        click.echo(f"- {participant[0]}")
    
    # Get images
    cursor.execute("""
    SELECT Images.Id, Images.Prompt, Users.Name
    FROM Images
    JOIN Users ON Images.User_Id = Users.Id
    WHERE Images.Game_Id = ?
    """, (game_id,))
    images = cursor.fetchall()
    
    click.echo("Images:")
    for image in images:
        click.echo(f"Image ID: {image[0]}, Prompt: {image[1]}, Created by: {image[2]}")
    
    conn.close()

@cli.command()
@click.argument('image_id', type=int)
def image_details(image_id):
    """View details of a specific image."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT Images.Id, Images.Prompt, Users.Name, Game.Id, VectorIndex.Id
    FROM Images
    JOIN Users ON Images.User_Id = Users.Id
    JOIN Game ON Images.Game_Id = Game.Id
    LEFT JOIN VectorIndex ON Images.Vector_Id = VectorIndex.Id
    WHERE Images.Id = ?
    """, (image_id,))
    image = cursor.fetchone()
    
    if not image:
        click.echo(f"No image found with ID {image_id}")
        return
    
    click.echo(f"Image ID: {image[0]}")
    click.echo(f"Prompt: {image[1]}")
    click.echo(f"Created by: {image[2]}")
    click.echo(f"Game ID: {image[3]}")
    click.echo(f"Vector ID: {image[4] if image[4] else 'Not available'}")
    
    conn.close()

if __name__ == '__main__':
    cli()
