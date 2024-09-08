-- Create Users table
CREATE TABLE IF NOT EXISTS Users (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Password TEXT NOT NULL
);

-- Create Game table
CREATE TABLE IF NOT EXISTS Game (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Winner_Id INTEGER,
    FOREIGN KEY (Winner_Id) REFERENCES Users(Id)
);

-- Create Images table
CREATE TABLE IF NOT EXISTS Images (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Prompt TEXT NOT NULL,
    Game_Id INTEGER NOT NULL,
    User_Id INTEGER NOT NULL,
    Vector_Id INTEGER,
    FOREIGN KEY (Game_Id) REFERENCES Game(Id),
    FOREIGN KEY (User_Id) REFERENCES Users(Id),
    FOREIGN KEY (Vector_Id) REFERENCES VectorIndex(Id)
);

-- Create VectorIndex table
CREATE TABLE IF NOT EXISTS VectorIndex (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Vector_embeddings BLOB NOT NULL,
    Image_Id INTEGER NOT NULL,
    FOREIGN KEY (Image_Id) REFERENCES Images(Id)
);

-- Create GameParticipants table
CREATE TABLE IF NOT EXISTS GameParticipants (
    Game_Id INTEGER NOT NULL,
    User_Id INTEGER NOT NULL,
    PRIMARY KEY (Game_Id, User_Id),
    FOREIGN KEY (Game_Id) REFERENCES Game(Id),
    FOREIGN KEY (User_Id) REFERENCES Users(Id)
);

-- Optional: Add some initial data
INSERT INTO Users (Name, Password) VALUES ('Mai', '123');
INSERT INTO Users (Name, Password) VALUES ('Domzi', '123');
INSERT INTO Users (Name, Password) VALUES ('Ana', '123');

