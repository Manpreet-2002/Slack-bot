from time import thread_time, thread_time_ns
import slack
import re,os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask,request,Response
from slackeventsapi import SlackEventAdapter
from slack_sdk.errors import SlackApiError
from datetime import datetime,timedelta
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote  
import logging
import sqlite3
import numpy as np
import pandas as pd
from rake_nltk import Rake
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
api = Api(app)

slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)

my_channel = os.environ['MY_CHANNEL']
my_password = os.environ['MY_PASSWORD']

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///messages_database.db'
db = SQLAlchemy(app)

logger = logging.getLogger(__name__)

class MessageModel(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	channel_id = db.Column(db.String(100), nullable=False)
	user_id = db.Column(db.String(100), nullable=False)
	text = db.Column(db.String(500), nullable=False)
	message_ts = db.Column(db.String(100), nullable=False)

	def __repr__(self):
		return f"User_Message(User_ID = {user_id}, Channel_ID = {channel_id}, Message_TS = {message_ts})"

#db.create_all()

resource_fields = {
	'id': fields.Integer,
	'subject': fields.String,
	'description': fields.String,
	'likes': fields.Integer
}

# ID of "text" channel that the message exists in
conversation_id = "C03KNQMGF7W" 

try:
    # Call the conversations.history method using the WebClient
    # The client passes the token you included in initialization    
    result = client.conversations_history(
        channel=conversation_id,
        inclusive=True,
    )

    for message in result["messages"]:
        if message['user'] != BOT_ID:
            new_msg = MessageModel(user_id=message['user'], message_ts=message['ts'], text=message['text'], channel_id=conversation_id)
            db.session.add(new_msg)
            db.session.commit()

except SlackApiError as e:
    print(f"Error: {e}")

@slack_event_adapter.on('message')
def get_similar_message(message):
    #print(message)
    event = message.get('event',{})
    print(event)
    channel_id = event.get('channel')
    user = event.get('user')
    text = event.get('text')
    ts = event.get('ts')
    result = MessageModel.query.filter_by(message_ts=ts).first()

    if user != BOT_ID and not result:
        # Create your connection.
        cnx = sqlite3.connect('messages_database.db')
        df3 = pd.read_sql_query("SELECT id, text FROM message_model", cnx)

        new_row = pd.DataFrame({'id': 0, 'text': text}, index=[0])
        df = pd.concat([new_row,df3.loc[:]]).reset_index(drop=True)

        # remove webpages/links and replace with empty space:
        parse_tweets=[]

        for i in range(len(df['text'])):

                patt=r'https?://\S+'
                rt=re.compile(patt)
                parse_tweets.append(rt.sub('', df['text'][i]))

        #print(parse_tweets[:2]) 

        # Create the Document Term Matrix
        count_vectorizer = CountVectorizer(stop_words='english')
        count_vectorizer = CountVectorizer()
        sparse_matrix = count_vectorizer.fit_transform(parse_tweets)

        # OPTIONAL: Convert Sparse Matrix to DF
        doc_term_matrix = sparse_matrix.todense()
        df2 = pd.DataFrame(doc_term_matrix, 
                        columns=count_vectorizer.get_feature_names()) 

        dj=pd.DataFrame(cosine_similarity(df2, dense_output=True))
        #print(dj.head())
        t=[]

        # Part 01:
        for j,k in enumerate(dj.values):
            for n in range(len(k)):
                t.append([j,n,k[n]])

        # Part 02:
        qq=[]
        for i in range(len(t)):
            if t[i][0]==t[i][1]:
                qq.append([t[i][0],t[i][1],0])
            else:
                qq.append(t[i])
        #print(qq[:5])
        u=defaultdict(list)

        # Part 01:

        for i in range(len(qq)):
            u[qq[i][0]].append(qq[i][2])
            
        updated_df=pd.DataFrame(u)

        threshold = 0.5
        ids_above_threshold = []
        number_of_ids = 3
        position_maxVal = np.argmax(updated_df[0])

        result2 = MessageModel.query.filter_by(id=position_maxVal).first()

        new_msg = MessageModel(user_id=user, message_ts=ts, text=text, channel_id=conversation_id)
        db.session.add(new_msg)
        db.session.commit()


        similar_query = client.chat_getPermalink(token='SLACK_TOKEN' , channel=conversation_id, message_ts='1655233788.378239')
        print(similar_query)


if __name__ == "__main__":
    app.run(debug=True)