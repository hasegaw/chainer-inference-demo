function init_websocket(url, dict)
{
    var ws = new WebSocket(url);

    ws.onopen = function(){
    }
 
    ws.onmessage = function(message){
        data_list = JSON.parse(message.data)
        for (var data of data_list) {
            ws.q.push([ws, data]);
            ws.num_images_current += 1;
        }
    }
 
    ws.onerror = function(){
    }
 
    ws.onclose = function(){
        $("#log").prepend("&lt;onclose&gt; " + "<br/>");
    }
 
    $(window).unload(function() {
        ws.onclose(); // WebSocket close
    })

    ws.holder = dict['holder'];
    ws.status_div = dict['status_div'];
    ws.rows = dict['rows'];
    ws.cols = dict['cols'];
    ws.q = [];
    ws.num_images_last = 0;
    ws.num_images_current = 0;
    ws.div = null;

    queues.push(ws);
} 
