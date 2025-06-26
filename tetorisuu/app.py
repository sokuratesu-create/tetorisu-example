from flask import Flask, render_template,redirect,request
import random

app = Flask(__name__)

board = None
game_over = False

ROWS = 22
COLS = 12

def init_board():
    global board 
    board = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            if r == 0 or r == ROWS - 1 or c == 0 or c == COLS - 1:
                row.append("wall")
            else:
                row.append("empty")
        board.append(row)

init_board()

def place_mino(board,mino_shape,color,offset=(1,5)):
    for dr,dc in mino_shape:
        r = offset[0] + dr
        c = offset[1] + dc
        board[r][c] = color
    return board

MINOS = {
    "I":{
        "shape":[[0,0],[1,0],[2,0],[3,0]],
        "color":"cyan"
    },
    "O":{
        "shape":[[0,0],[0,1],[1,0],[1,1]],
        "color":"yellow"
    },
    "T":{
        "shape":[[0,1],[1,0],[1,1],[1,2]],
        "color":"purple"
    },
    "S":{
        "shape":[[0,1],[0,2],[1,0],[1,1]],
        "color":"green"
    },
    "Z":{
        "shape":[[0,0],[0,1],[1,1],[1,2]],
        "color":"red"
    },
    "J":{
        "shape":[[0,0],[1,0],[2,0],[2,1]],
        "color":"blue"
    },
    "L":{
        "shape":[[0,1],[1,1],[2,1],[2,0]],
        "color":"orange"
    },
}

current_mino = None
current_offset = [1,5]

def spawn_random_mino():
    global current_mino, current_offset, game_over
    mino_type = random.choice(list(MINOS.keys()))
    current_mino = MINOS[mino_type]
    current_offset = [1, 5]  # 初期位置

    # 出現できない位置ならゲームオーバー
    if not is_valid_position(board, current_mino["shape"], current_offset):
        game_over = True

def step_down():
    global current_offset
    new_offset = [current_offset[0] + 1, current_offset[1]]
    if is_valid_position(board, current_mino["shape"], new_offset):
        current_offset = new_offset
    else:
        # 衝突 → 固定して新ミノへ
        lock_mino()
        clear_lines() #ライン消去
        spawn_random_mino()

def rotate_current_mino(board):
    shape = current_mino["shape"]
    rotated = [[dc,-dr] for dr,dc in shape]
    if is_valid_position(board,rotated,current_offset):
        current_mino["shape"] = rotated

def is_valid_position(board,shape,offset):
    for dr,dc in shape:
        r = offset[0] + dr
        c = offset[1] + dc
        if not (0<=r<ROWS and 0<=c<COLS):
            return False
        if board[r][c] != "empty":
            return False
    return True

def lock_mino():
    global board
    for dr,dc in current_mino["shape"]:
        r = current_offset[0] + dr
        c = current_offset[1] + dc
        board[r][c] = current_mino["color"]

def clear_lines():
    global board
    new_board = []

    for row in board[1:-1]:  # 壁を除いた中身だけチェック（上下の壁は除く）
        # 中央部（1~10列目）がすべて埋まっているかチェック
        if all(cell != "empty" for cell in row[1:-1]):
            # 消す対象：スキップ（行を入れない）
            continue
        else:
            new_board.append(row)

    # 消された分だけ空行を上から追加
    lines_cleared = (ROWS - 2) - len(new_board)  # 実際の高さ - 現在の行数
    empty_row = ["wall"] + ["empty"] * (COLS - 2) + ["wall"]
    for _ in range(lines_cleared):
        new_board.insert(0, empty_row[:])  # 新しい空行（コピー）を挿入

    # 上下の壁を戻す
    board = [["wall"] * COLS] + new_board + [["wall"] * COLS]

@app.route("/")
def index():
    global current_mino
    if current_mino is None:
        spawn_random_mino()

    display_board = [row[:] for row in board]
    if not game_over:
        display_board = place_mino(display_board, current_mino["shape"], current_mino["color"], current_offset)
    return render_template("index.html", board=display_board, auto_fall=not game_over, game_over=game_over)

@app.route("/step")
def step():
    if not game_over:
        step_down()
    display_board = [row[:] for row in board]
    if not game_over:
        display_board = place_mino(display_board, current_mino["shape"], current_mino["color"], current_offset)
    return render_template("index.html", board=display_board, auto_fall=not game_over, game_over=game_over)

@app.route("/move", methods=["POST"])
def move():
    direction = request.form.get("direction")
    if direction == "left":
        new_offset = [current_offset[0], current_offset[1] - 1]
        if is_valid_position(board, current_mino["shape"], new_offset):
            current_offset[1] -= 1
    elif direction == "right":
        new_offset = [current_offset[0], current_offset[1] + 1]
        if is_valid_position(board, current_mino["shape"], new_offset):
            current_offset[1] += 1
    elif direction == "rotate":
        rotate_current_mino(board)

    # ↓ ここでリダイレクトやめて、そのまま描画して再度 auto_fall 有効化！
    display_board = [row[:] for row in board]
    display_board = place_mino(display_board, current_mino["shape"], current_mino["color"], current_offset)
    return render_template("index.html", board=display_board, auto_fall=True)

if __name__ == "__main__":
    app.run(debug=True)