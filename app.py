from flask import Flask, request, jsonify, render_template
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask_sse import sse
from redis import Redis

# Database setup
engine = create_engine('sqlite:///messages.db')
Base = declarative_base()

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    message = Column(String)

Base.metadata.create_all(engine)

app = Flask(__name__)
app.config["REDIS_URL"] = "redis://localhost:6379"
app.register_blueprint(sse, url_prefix='/stream')

redis = Redis.from_url(app.config["REDIS_URL"])

Session = sessionmaker(bind=engine)
session = Session()

@app.route("/", methods=['GET'])
def index():
    return render_template('index.html')

@app.route("/send_message", methods=['POST'])
def send_message():
    data = request.get_json()
    if data and 'message' in data:
        new_message = Message(message=data['message'])
        session.add(new_message)
        session.commit()
        sse.publish({'message': data['message']}, type='greeting')
        return jsonify({"status": "Message received"}), 200
    return jsonify({"status": "Bad request"}), 400

@app.route("/get_messages", methods=['GET'])
def get_messages():
    messages = session.query(Message).all()
    return jsonify(messages=[message.message for message in messages])

if __name__ == "__main__":
    app.run(debug=True)
