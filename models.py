from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
        }
    
class ChattingRoom(db.Model):
    __tablename__ = 'chatting_room'
    room_id = db.Column(db.Integer,primary_key=True, autoincrement=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) ##신고자 아이디
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) ##물건 주인 아이디

class ChattingMessage(db.Model):
    __tablename__ = 'chatting_message'
    message_id = db.Column(db.Integer,primary_key=True, autoincrement=True)
    chattingroom_id = db.Column(db.Integer, db.ForeignKey('chatting_room.room_id'), nullable=False)
    message = db.Column(db.String(255))
    date = db.Column(db.String(255))
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)