import streamlit as st
import chess
import random
from typing import Tuple

st.set_page_config(page_title="Warhammer Chess", page_icon="♟", layout="centered")

WH_WHITE = {
    chess.KING:  ("EM", "Emperor"),
    chess.QUEEN: ("IN", "Inquisitor"),
    chess.ROOK:  ("DR", "Dreadnought"),
    chess.BISHOP:("LB", "Librarian"),
    chess.KNIGHT:("AM", "Assault Marine"),
    chess.PAWN:  ("GD", "Guardsman"),
}
WH_BLACK = {
    chess.KING:  ("WM", "Warmaster"),
    chess.QUEEN: ("DP", "Daemon Prince"),
    chess.ROOK:  ("HB", "Hellbrute"),
    chess.BISHOP:("SC", "Sorcerer"),
    chess.KNIGHT:("CB", "Chaos Biker"),
    chess.PAWN:  ("CT", "Cultist"),
}

PIECE_VALUE = {
    chess.KING: 10000,
    chess.QUEEN: 900,
    chess.ROOK: 500,
    chess.BISHOP: 330,
    chess.KNIGHT: 320,
    chess.PAWN: 100,
}

def piece_label(piece: chess.Piece) -> Tuple[str, str]:
    if not piece:
        return ("", "")
    table = WH_WHITE if piece.color == chess.WHITE else WH_BLACK
    code, name = table[piece.piece_type]
    return (code, name)

if "board" not in st.session_state:
    st.session_state.board = chess.Board()
if "selected" not in st.session_state:
    st.session_state.selected = None
if "moves_log" not in st.session_state:
    st.session_state.moves_log = []

board: chess.Board = st.session_state.board

st.sidebar.title("Warhammer Chess")
if st.sidebar.button("New Game"):
    st.session_state.board = chess.Board()
    st.session_state.selected = None
    st.session_state.moves_log = []
    board = st.session_state.board

bot_side = st.sidebar.selectbox("Easy bot plays", ["Chaos (black)", "Imperium (white)", "Off"])
show_legal = st.sidebar.checkbox("Show legal moves", value=True)

st.sidebar.markdown("### Legend")
for pt in [chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]:
    st.sidebar.write(f"{WH_WHITE[pt][0]} = {WH_WHITE[pt][1]} [Imperium]")
for pt in [chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]:
    st.sidebar.write(f"{WH_BLACK[pt][0]} = {WH_BLACK[pt][1]} [Chaos]")

def easy_bot_move(b: chess.Board):
    best_score = -1
    best_moves = []
    for mv in b.legal_moves:
        score = 0
        if b.is_capture(mv):
            captured = b.piece_at(mv.to_square)
            if captured:
                score += PIECE_VALUE[captured.piece_type]
        score += random.random() * 5
        if score > best_score:
            best_score = score
            best_moves = [mv]
        elif score == best_score:
            best_moves.append(mv)
    if not best_moves:
        return None
    return random.choice(best_moves)

def square_color(file_idx, rank_idx):
    return "#edebe9" if (file_idx + rank_idx) % 2 == 0 else "#b7b7b7"

def click_square(sq_index):
    if st.session_state.selected is None:
        piece = board.piece_at(sq_index)
        if piece and piece.color == board.turn:
            st.session_state.selected = sq_index
    else:
        src = st.session_state.selected
        dst = sq_index
        mv = chess.Move(src, dst)
        if board.piece_at(src) and board.piece_at(src).piece_type == chess.PAWN:
            rank = chess.square_rank(dst)
            if (board.turn and rank == 7) or ((not board.turn) and rank == 0):
                mv = chess.Move(src, dst, promotion=chess.QUEEN)
        if mv in board.legal_moves:
            san = board.san(mv)
            board.push(mv)
            st.session_state.moves_log.append(san)
        st.session_state.selected = None

def maybe_bot_move():
    side = "Off"
    if bot_side == "Chaos (black)":
        side = "black"
    elif bot_side == "Imperium (white)":
        side = "white"
    if side == "Off":
        return
    if (side == "white" and board.turn == chess.WHITE) or (side == "black" and board.turn == chess.BLACK):
        mv = easy_bot_move(board)
        if mv:
            san = board.san(mv)
            board.push(mv)
            st.session_state.moves_log.append(san)

st.title("Warhammer Chess")
st.caption("Imperium to move" if board.turn == chess.WHITE else "Chaos to move")

if board.is_game_over():
    result = board.result()
    if result == "1-0":
        st.success("Checkmate. Imperium wins.")
    elif result == "0-1":
        st.success("Checkmate. Chaos wins.")
    else:
        st.info("Draw.")

files = range(8)
ranks = range(7, -1, -1)
selected = st.session_state.selected
legal_targets = set()

if selected is not None and show_legal:
    for mv in board.legal_moves:
        if mv.from_square == selected:
            legal_targets.add(mv.to_square)

for r in ranks:
    cols = st.columns(8, gap="small")
    for f in files:
        sq = chess.square(f, r)
        piece = board.piece_at(sq)
        label, name = piece_label(piece)
        is_sel = (selected == sq)
        bg = square_color(f, r)
        if is_sel:
            bg = "#f7dc6f"
        elif sq in legal_targets:
            bg = "#82e0aa"
        style = f"background-color:{bg}; border:1px solid #555; height:60px; display:flex; align-items:center; justify-content:center; font-weight:600;"
        if piece:
            txt_color = "#1b4f72" if piece.color == chess.WHITE else "#641e16"
            style += f" color:{txt_color};"
        with cols[f]:
            if st.button(label if label else " ", key=f"{sq}", help=name, use_container_width=True):
                if not board.is_game_over():
                    click_square(sq)
                    if not board.is_game_over():
                        maybe_bot_move()

st.markdown("### Moves")
if st.session_state.moves_log:
    pairs = []
    temp = st.session_state.moves_log[:]
    i = 0
    while i < len(temp):
        white_move = temp[i]
        black_move = temp[i+1] if i+1 < len(temp) else ""
        pairs.append((len(pairs)+1, white_move, black_move))
        i += 2
    cols = st.columns([1,3,3])
    cols[0].write("No.")
    cols[1].write("Imperium")
    cols[2].write("Chaos")
    for idx, wm, bm in pairs:
        cols = st.columns([1,3,3])
        cols[0].write(str(idx))
        cols[1].write(wm)
        cols[2].write(bm)
else:
    st.write("No moves yet.")

st.caption("Tip: click a piece, then its destination square. Pawns auto promote to Inquisitor for speed.")
