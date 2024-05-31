$(document).ready(function() {
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
    var username=usercurrent;
    var room_id=roomcurrent;
    var userid;

    console.log(room_id);
    loadMessages();

    function loadMessages() {
        $.getJSON(`/messages/${room_id}`, function(messages) {
            messages.forEach(function(msg) {
                fetchUserData(username,msg);
            });
        }).fail(function(jqXHR, textStatus, errorThrown) {
            console.error('Error loading messages: ' + textStatus);
        });
    }


    function displaychattinglist(msg) {
        var containerClass = msg.sender_id === userid ? 'r-container' : 'l-container';
        var userNameClass = msg.sender_id === userid ? 'rightuser' : 'leftuser';
        var containerDiv = $(`<div class="${containerClass}"></div>`);
        var timeDiv = $(`<div class="time">${msg.time}</div>`);
        var messageDiv = $(`<div class="${userNameClass}">${msg.message}</div>`);
        
        if(msg.sender_id===userid){
            containerDiv.append(timeDiv);
            containerDiv.append(messageDiv);
            $('.left-content').append(containerDiv);
        }
        else{
            var rname = $(`<div class="opponent-id">${msg.sender_name}</div>`);
            $('.left-content').append(rname);
            containerDiv.append(messageDiv);
            containerDiv.append(timeDiv);
            $('.left-content').append(containerDiv);
        }
        
        let content = $('.left-content');
        content.scrollTop(content[0].scrollHeight);
    }

    function fetchUserData(username,msg) {
        fetch(`/api/users/${username}`)
            .then(response => response.json())
            .then(data => {
                console.log('User Data:', data);
                userid=data.id;
                displaychattinglist(msg);
            })
            .catch(error => console.error('Error fetching data:', error));
    }
    
    
    
    socket.on('connect', function() {
        console.log('Connected to the server.');
    });

    socket.on('receive_message', function(data) {
        console.log('Received message:', data);
        displayMessage(data,room_id);
    });

    $('.left-button').click(function() {
        var message = $('.left-inputtxt').val();
        if (message.trim() !== '') {
            var currentTime = getCurrentTime();
            var messageData = {
                user: username,
                time: currentTime,
                chat: message,
                room_id: room_id,
            };
            let containerdiv = $('<div class="r-container"></div>');
            let timediv = $('<div class="time">' + currentTime + '</div>');
            let userdiv = $('<div class="rightuser"></div>').html(message);
            containerdiv.append(timediv);
            containerdiv.append(userdiv);
            $('.left-content').append(containerdiv);
            let content=$('.left-content');
            content.scrollTop(content[0].scrollHeight);

            socket.emit('send_message', messageData);
            $('.left-inputtxt').val('');
        }
    });
    function displayMessage(data,room_id) {    
        if(data.room_id==room_id&&data.receiver_name==username){
            // 상대방이 보낸 메시   
            let rname = $('<div class="opponent-id">' + data.sender_name + '</div>');
            $('.left-content').append(rname);
            let containerdiv2 = $('<div class="l-container"></div>');
            let timediv2 = $('<div class="time">' + data.time + '</div>');
            let userdiv2 = $('<div class="leftuser">'+data.message+'</div>');
            containerdiv2.append(userdiv2);
            containerdiv2.append(timediv2);
            $('.left-content').append(containerdiv2);
        
            let content2=$('.left-content');
            content2.scrollTop(content2[0].scrollHeight);
        }
    
    
        let content = $('.left-content');
        content.scrollTop(content[0].scrollHeight);
    }
});



function getCurrentTime() {
    // 현재 시간을 '오전/오후 시:분' 형식으로 반환
    let time = new Date();
    let hour = time.getHours();
    let minute = time.getMinutes();
    let flag = hour >= 12 ? '오후' : '오전';
    hour = hour % 12;
    hour = hour ? hour : 12;  // '0' hour should be '12'
    minute = minute < 10 ? '0' + minute : minute;
    return flag + ' ' + hour + ':' + minute;
}