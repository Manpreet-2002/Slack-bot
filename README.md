![SLACK__BOT_🤖](https://user-images.githubusercontent.com/79961524/179845326-a8398934-fbbb-4ff2-b3a9-02514e46ccb8.png)

Technologies Used -> Flask framework, RESTful API, SLACK API 

Database Used -> SQLite, SQLAlchemy(ORM)

ML Libraries -> SK-Learn

```Bot2.py``` fetches all the messages in channels:history and checks if messages are not sent by the bot and then populates the fields -> user_id, channel_id, message_ts
(messages timestamp) and text (the actual message) of an SQLite database that is managed by the ORM - SQLAlchemy. 

A slack-event-adapter decorator has been added to a function which gets triggered whenever a new message is sent to a channel. 

This function first checks if the bot itself hasn't replied and then gets the most similar message which is already stored in the database.

This similarity check has been implemented using cosine similarity.

First the text message is searched for hyperlinks and are replaced by blank strings. Then a sparse matrix is obtained for all the messages in the database using ```Count Visualizer``` 
of SK-Learn's feature extraction library.

Then SK-Learn's ```cosine similarity``` is called pairwise and we search the message which has max value of similarity (closest to 1) for the given message and return it.

![image](https://user-images.githubusercontent.com/79961524/179845570-017013a6-88a1-4f9a-8d98-e75c021eb930.png)
