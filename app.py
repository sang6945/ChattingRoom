from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, send, emit
from sqlalchemy.exc import IntegrityError
import datetime
from models import db, User, ChattingRoom, ChattingMessage
from sqlalchemy import func


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('user_register.html')


@app.route('/chat_rooms')
def chat_rooms():
    username = request.args.get('username')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # 마지막 메시지 정보를 가져오기 위한 Subquery 생성
    last_message_subquery = db.session.query(
        ChattingMessage.chattingroom_id,
        func.max(ChattingMessage.message_id).label('max_message_id')
    ).group_by(ChattingMessage.chattingroom_id).subquery()

    # 채팅방과 마지막 메시지 정보 로드
    rooms = db.session.query(
        ChattingRoom.room_id,
        ChattingRoom.reporter_id,
        ChattingRoom.owner_id,
        ChattingMessage.message.label('last_message'),
        ChattingMessage.date.label('last_message_date')
    ).outerjoin(
        last_message_subquery,
        ChattingRoom.room_id == last_message_subquery.c.chattingroom_id
    ).outerjoin(
        ChattingMessage,
        ChattingMessage.message_id == last_message_subquery.c.max_message_id
    ).filter(
        (ChattingRoom.reporter_id == user.id) | (ChattingRoom.owner_id == user.id)
    ).all()

    enhanced_rooms = []
    for room in rooms:
        other_user = User.query.filter_by(id=room.reporter_id).first().username if room.owner_id == user.id else User.query.filter_by(id=room.owner_id).first().username
        enhanced_rooms.append({
            'room_id': room.room_id,
            'other_user': other_user,
            'last_message': room.last_message if room.last_message else "No messages yet",
            'last_message_date': room.last_message_date if room.last_message_date else "No date available"
        })

    return render_template('chat_rooms.html', rooms=enhanced_rooms, username=username)

@app.route('/chat/<int:room_id>/<string:username>')
def chat(room_id, username):
    room = ChattingRoom.query.filter_by(room_id=room_id).first()
    user=User.query.filter_by(username=username).first()
    if not room:
        return "Room not found", 404
    messages = ChattingMessage.query.filter_by(chattingroom_id=room_id).order_by(ChattingMessage.date).all()
    print(user.username)
    return render_template('chat.html', room_id=room.room_id, messages=messages, username=user.username)

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.filter_by(username=user_id).first()
    if user:
        return jsonify(user.to_dict())
    else:
        return jsonify({"error": "User not found"}), 404
    
    
#####테스트용 임시로 user 등록
@app.route('/register', methods=['POST'])
def register_user():
    username = request.json.get('username')
    try:
        new_user = User(username=username)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully', 'user_id': new_user.id}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Username already exists'}), 400

@app.route('/create_room', methods=['POST'])
def create_chat_room():
    username = request.json.get('username')
    opponent_name = request.json.get('opponent')

    user = User.query.filter_by(username=username).first()
    opponent = User.query.filter_by(username=opponent_name).first()

    if not user or not opponent:
        return jsonify({'message': 'One or both users do not exist'}), 404

    # Reporter와 Owner결정 임시로 id의 대소비교로 결정. 실제로는 앞에서 결정됨.
    if user.id < opponent.id:
        reporter, owner = user, opponent
    else:
        reporter, owner = opponent, user

    # Check if a room already exists
    room = ChattingRoom.query.filter_by(reporter_id=reporter.id, owner_id=owner.id).first()
    if not room:
        room = ChattingRoom(
            reporter_id=reporter.id, 
            owner_id=owner.id,
        )
        db.session.add(room)
        db.session.commit()

    return jsonify({
        'message': 'Chat room created successfully',
        'room_id': room.room_id,
        'reporter_id': reporter.id,
        'owner_id': owner.id,
        'reporter_name': reporter.username,
        'owner_name': owner.username
    }), 201
    
@app.route('/messages/<int:room_id>')
def get_messages(room_id):
    messages = ChattingMessage.query.filter_by(chattingroom_id=room_id).order_by(ChattingMessage.date).all()
    message_list = [{
        'sender_id': msg.sender_id,
        'receiver_id': msg.receiver_id,
        'message': msg.message,
        'time': msg.date,
        'sender_name':User.query.filter_by(id=msg.sender_id).first().username,
    } for msg in messages]
    return jsonify(message_list)

@socketio.on('send_message')
def handle_message(data):
    room_id=data.get('room_id')
    sender_name = data.get('user')
    user=User.query.filter_by(username=sender_name).first()
    sender_id=user.id
    message_text = data.get('chat')
    date=data.get('time')
    
    room = ChattingRoom.query.filter_by(room_id=room_id).first()
    if not room:
        emit('error', {'error': 'Room not found'})
        return

    # sender_id와 다른 참여자 찾기
    if room.owner_id == sender_id:
        receiver_id = room.reporter_id
    elif room.reporter_id == sender_id:
        receiver_id = room.owner_id
    else:
        emit('error', {'error': 'Sender not part of the room'})
        return

    receiver=User.query.filter_by(id=receiver_id).first()
    if not all([room_id, sender_id, message_text, date]):
        emit('error', {'error': 'Missing required data fields'})
        return

    # 메시지 객체 생성 및 저장
    message = ChattingMessage(
        chattingroom_id=room_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        message=message_text,
        date=date,
    )
    db.session.add(message)
    db.session.commit()
    emit('receive_message', {
        'sender_id': sender_id,
        'receiver_id': receiver_id,
        'message': data['chat'],
        'time': data['time'],
        'room_id': room_id,
        'receiver_name':receiver.username,
        'sender_name':user.username,
    }, broadcast=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)