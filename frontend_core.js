ex = 70; //125;
ey = 70;

font_px = 11;
line_height = font_px + 2;


function draw_image(view, data)
{
    var ctx  = view.getContext("2d");
    var img_box = new Image();
    function img_box_loaded()
    {
        ctx.drawImage(img_box, 0, 0, img_box.width, img_box.height, 0, 0, ex, ey);
    }

    img_box.src = data["filename"];
    img_box.addEventListener('load', img_box_loaded, false);
}


function draw_probability(view, data)
{
    var ctx  = view.getContext("2d");
    ctx.font = "bold " + font_px + "px 'ＭＳ Ｐゴシック'";

    var i = 0;
    var img_x = ex;
    var img_y = ey;
    var y = 0;
    var num_top_classes = 5;
    var actual_class_label = "unknown"; // data['p'][Math.floor(Math.random()*5)][0];
    for (var p of data["p"]) {
        var label = p[0];
        var probability = Math.floor(p[1] * 1000) * 0.1;

        var y0 = img_y + y * line_height;
        var y2 = y0 + line_height;

        var x1 = ex * probability * 0.01;

        var style1;
        var style2;

        if (label == actual_class_label) {
            // 正しいクラスの場合のスタイル
            style1 = "rgb(40, 190, 40)";
            style2 = "rgb(0, 0, 0)";
        } else {
            // 間違ったクラスの場合のスタイル
            style1 = "rgb(255, 100, 100)";
            style2 = "rgb(0, 0, 0)";
        }
            
        ctx.fillStyle=(style1);
        ctx.fillRect(0, y0, x1, line_height);
        ctx.fillStyle=(style2);
        ctx.fillRect(x1, y0, ex - x1, line_height);

        ctx.fillStyle="#ccc"
        ctx.fillText(label, 2, y0 + font_px);
        y += 1;

        if (y > num_top_classes) break;
    }
}


function create_canvas()
{
    var canvas = document.createElement("canvas");
    canvas.height = ey + 5 * line_height;  //サイズ　縦
    canvas.width = ex;                     //サイズ　横

    var ctx = canvas.getContext("2d");

    return canvas;
}



/////////////////////////////////////////////////////////////////////

var div = null;

var queues = [];

function set_draw_timer()
{
    setTimeout(draw_handler, 1);
}

function draw_handler()
{
    var i;

    for (i = 0; i < queues.length; i++) {
        if (queues[i].q.length > 200) {
            // たまりすぎている
            for (var j = 0; j < queues.length; j++) {
                queues[j].q = []
            }

        }
        if (queues[i].q.length != 0) {
            var tuple = queues[i].q.pop();

            var ws = tuple[0];
            var data = tuple[1];

            receive1(ws, data);
        }
    }
    set_draw_timer();
}


function set_throughput_timer()
{
    setTimeout(timer_handler, 10000);
}

function timer_handler()
{
    var i = 0;
    var s = "";
    for (i = 0; i < queues.length; i++) {
        var delta = (queues[i].num_images_current - queues[i].num_images_last) / 10;
        queues[i].num_images_last = queues[i].num_images_current;

        s = Math.round(delta*10)/10 + " Images/sec<br>";
        queues[i].status_div.innerHTML=s;
    }

    document.getElementById("summary").innerHTML = s;
    set_throughput_timer();
}



function goBottom(targetId) {
    var obj = document.getElementById(targetId);
    if(!obj) return;
    obj.scrollTop = obj.scrollHeight;
}

function receive1(ws, d) {
    var holder = ws.holder
    // 最後のエレメントもしくは次の div を創る
    if (ws.div == null || ws.div.childNodes.length >= ws.cols) {
        ws.div = document.createElement("div");
        holder.appendChild(ws.div);

        lines = holder.getElementsByTagName("div")
        if (lines.length > ws.rows) {
            holder.removeChild(lines[0]);
        }
    }

    var canvas = create_canvas();
    ws.div.appendChild(canvas);
    draw_image(canvas, d);
    draw_probability(canvas, d);

    // 最後にスクロールダウン
    //goBottom('body');
}

set_draw_timer();
set_throughput_timer();
