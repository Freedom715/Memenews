var ma = {{messages[-1].id}};

function send_message() {
var input = document.getElementById("textInput");
$.ajax({
            url: '/api/v2/messages',
            type: 'post',
            data: {"text": input.value, "user_from_id": {{current_user.id}},
             "user_to_id": {{user_to.id}} },
            response:'json',
            success: function(data) {mode();
                                     input.value = ""},
        });
};

function get_time(time) {
    var time_input = time.split(" ")[1];
    var date_input = time.split(" ")[0];

    var months = {1: "Января", 2: "Февраля", 3: "Марта", 4: "Апреля", 5: "Мая", 6: "Июня", 7: "Июля",
          8: "Августа", 9: "Сентября", 10: "Октября", 11: "Ноября", 12: "Декабря"};
    var year = Number(String(date_input).split("-")[0]);
    var month = Number(String(date_input).split("-")[1]);
    var day = Number(String(date_input).split("-")[2]);
    var current_date_time = new Date();
    var minute = Number(String(time_input).split(":")[0]);
    var second = Number(String(time_input).split(":")[1]);
    if (day == current_date_time.getDate()){
        return ("Сегодня в " + [ minute, second ].join(":"))}
    else if ((day + 1) == current_date_time.getDate()){
        return ("Вчера в " + [ minute, second ].join(":"))}
    else{
        return (String(day) + " " + months[Number(month)] + " " + String(year) + " в " + [minute, second].join(":"))}
};
function mode() {
var form = document.getElementById("mess");
var input = document.getElementById("textInput");
    $.ajax({
            url: '/api/v2/messages',
            type: 'GET',
            dataType : "json",
            success: function(messages) {
<!--            form.innerHTML = "";-->
            $.each(messages.messages, function(i, val) {
            if (val.id > ma){
                if (val.user_from_id == {{current_user.id}} && val.user_to_id == {{user_to.id}}) {
                    var ref = document.createElement("a");
                    ref.href = "/profile/{{current_user.id}}";
                    ref.name = val.id;
                    var img = document.createElement("img");
                    img.src = "{{current_user.avatar}}";
                    img.className = "align-self-center mr-3 rounded-lg";
                    img.alt = "PEP8";
                    img.width = "100";
                    img.height = "100";
                    img.title = "{{current_user.name}}";
                    img.name = val.id;
                    ref.appendChild(img);
                    var message = document.createElement("div");
                    message.className = "media block rounded-lg";
                    var media_block = document.createElement("div");
                    media_block.className = "media-body"
                    media_block.innerHTML = '<h5 class="mt-0">{{current_user.name}}</h5>';
                    var text = document.createElement("p");
                    text.className = "text-break";
                    text.innerHTML = val.text;
                    media_block.appendChild(text);
                    var button = document.createElement("a");
                    button.className = "btn-sm btn-danger";
                    button.text = "Удалить";
                    button.href="/message_delete/" + val.id;
                    media_block.appendChild(document.createTextNode(get_time(val.time)));
                    media_block.appendChild(document.createElement("br"));
                    media_block.appendChild(button);
                    media_block.appendChild(document.createElement("br"));
                    message.appendChild(ref);
                    message.appendChild(media_block);
                    form.appendChild(message)
                    if (val.id > ma) {ma = val.id}
                } else if (val.user_to_id == {{current_user.id}} && val.user_from_id == {{user_to.id}}){
                    var ref = document.createElement("a");
                    ref.href = "/profile/{{current_user.id}}";
                    ref.name = val.id;
                    var img = document.createElement("img");
                    img.src = "{{user_to.avatar}}";
                    img.className = "align-self-center mr-3 rounded-lg";
                    img.alt = "PEP8";
                    img.width = "100";
                    img.height = "100";
                    img.title = "{{user_to.name}}";
                    img.hspace= "20";
                    ref.appendChild(img);
                    var message = document.createElement("div");
                    message.className = "media block rounded-lg";
                    var media_block = document.createElement("div");
                    media_block.className = "media-body"
                    media_block.innerHTML = '<h5 class="mt-0" align="right">{{user_to.name}}</h5>';
                    var text = document.createElement("p");
                    text.className = "text-break text-right";
                    text.innerHTML = val.text + "<br>";
                    text.appendChild(document.createTextNode(get_time(val.time)));
                    media_block.appendChild(text);
                    media_block.appendChild(document.createElement("br"));
                    media_block.appendChild(document.createElement("br"));
                    message.appendChild(media_block);
                    message.appendChild(ref);
                    form.appendChild(message)
                    if (val.id > ma) {ma = val.id}
                }
                }
            }
            });
            if (window.location.hash != "#" + ma)
                {$(function(){ window.location.hash = ma; });}
                input.focus();
                }
            });


};
mode();
setInterval(mode, 3000);
</script>
{% endblock %}