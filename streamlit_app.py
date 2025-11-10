import streamlit as st
import random
import json
import streamlit.components.v1 as components

st.title("🎲 4명의 학생 주사위 게임")
st.write("4명의 학생이 차례대로 주사위를 굴려 나온 수만큼 이동합니다. 전체 칸 수는 30칸입니다.")

BOARD_SIZE = 30
PLAYER_COUNT = 4

# 세션 상태 초기화
if "positions" not in st.session_state:
    st.session_state.positions = [0] * PLAYER_COUNT  # 0 = 시작점, 1..30 = 칸
if "current_player" not in st.session_state:
    st.session_state.current_player = 0
if "last_roll" not in st.session_state:
    st.session_state.last_roll = None
if "winner" not in st.session_state:
    st.session_state.winner = None
if "history" not in st.session_state:
    st.session_state.history = []  # (player, roll, new_pos)

def roll_dice():
    if st.session_state.winner is not None:
        return
    roll = random.randint(1, 6)
    p = st.session_state.current_player
    new_pos = min(BOARD_SIZE, st.session_state.positions[p] + roll)
    st.session_state.positions[p] = new_pos
    st.session_state.last_roll = roll
    st.session_state.history.append((p + 1, roll, new_pos))
    if new_pos >= BOARD_SIZE:
        st.session_state.winner = p + 1
    else:
        st.session_state.current_player = (p + 1) % PLAYER_COUNT

def reset_game():
    st.session_state.positions = [0] * PLAYER_COUNT
    st.session_state.current_player = 0
    st.session_state.last_roll = None
    st.session_state.winner = None
    st.session_state.history = []

def render_board():
    # Render an HTML 5x6 table (rows=5, cols=6) with numbered cells 1..BOARD_SIZE
    player_colors = ["#e74c3c", "#2980b9", "#27ae60", "#f39c12"]  # 빨강, 파랑, 초록, 주황

    # Prepare mapping of cell index -> list of players on that cell
    occupants = {i: [] for i in range(1, BOARD_SIZE + 1)}
    for i, pos in enumerate(st.session_state.positions):
        if pos >= 1:
            occupants[pos].append(i + 1)

    # Build HTML with overlay tokens and animation script
    positions_json = json.dumps(st.session_state.positions)
    player_colors_js = json.dumps(player_colors)
    last_roll_json = json.dumps(st.session_state.last_roll)

    html = """
    <style>
    .board-wrapper { position: relative; }
    .board { border-collapse: collapse; width: 100%; }
    .board td { border: 1px solid #ccc; width: 16.66%; height: 80px; vertical-align: top; padding: 6px; position: relative; }
    .cell-number { font-size: 12px; color: #666; position: absolute; top:6px; left:6px; }
    /* floating tokens overlay */
    .overlay { position: absolute; top:0; left:0; width:100%; height:100%; pointer-events: none; }
    .floating-token { position: absolute; width:28px; height:28px; border-radius:50%; color: #fff; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:600; box-shadow: 0 2px 6px rgba(0,0,0,0.15); border:2px solid #fff; transition: transform 450ms cubic-bezier(.2,.8,.2,1), left 450ms cubic-bezier(.2,.8,.2,1), top 450ms cubic-bezier(.2,.8,.2,1); transform: translateZ(0); }
    </style>

    <div class="board-wrapper">
        <table class="board">
    """

    cols = 6
    for r in range(5):
        html += "<tr>"
        for c in range(cols):
            idx = r * cols + c + 1
            if idx > BOARD_SIZE:
                html += "<td></td>"
                continue
            html += f"<td data-cell='{idx}'><div class='cell-number'>{idx}</div></td>"
        html += "</tr>"
    html += "</table>"

    # overlay container where floating tokens will be positioned and animated
    html += "<div class='overlay' id='overlay'></div>"

    # JavaScript: place tokens initially at previous positions (from localStorage) then animate to current positions
    html += """
    <script>
    (function(){
        const positions = __POSITIONS__;
        const colors = __COLORS__;
        const lastRoll = __LAST_ROLL__;
        const overlay = document.getElementById('overlay');
        const wrapper = document.querySelector('.board-wrapper');
        const tokenSize = 28;

        // helper to get cell center coords relative to wrapper
        function cellCenter(cellIndex){
            const cell = document.querySelector(`[data-cell='${cellIndex}']`);
            if(!cell) return null;
            const cRect = cell.getBoundingClientRect();
            const wRect = wrapper.getBoundingClientRect();
            const left = cRect.left - wRect.left + (cRect.width - tokenSize)/2;
            const top = cRect.top - wRect.top + (cRect.height - tokenSize)/2;
            return {left: left, top: top};
        }

        // read previous positions from localStorage
        let prev = null;
        try { prev = JSON.parse(localStorage.getItem('streamlit_positions') || 'null'); } catch(e){ prev = null; }

        // create tokens and place them at prev positions (or off-board if none)
        for(let i=0;i<positions.length;i++){
            const p = positions[i];
            const token = document.createElement('div');
            token.className = 'floating-token';
            token.id = 'token-' + (i+1);
            token.style.width = tokenSize + 'px';
            token.style.height = tokenSize + 'px';
            token.style.lineHeight = tokenSize + 'px';
            token.style.background = colors[i % colors.length];
            token.textContent = String(i+1);
            // initial position
            let startPos = null;
            if(prev && prev[i] >= 1) startPos = cellCenter(prev[i]);
            if(startPos){ token.style.left = startPos.left + 'px'; token.style.top = startPos.top + 'px'; }
            else { token.style.left = '-40px'; token.style.top = (10 + i*36) + 'px'; }
            overlay.appendChild(token);
        }

        // function to animate tokens to current positions and persist
        function animateTokens(){
            for(let i=0;i<positions.length;i++){
                const p = positions[i];
                const token = document.getElementById('token-' + (i+1));
                if(!token) continue;
                if(p >= 1){
                    const c = cellCenter(p);
                    if(c){ token.style.left = c.left + 'px'; token.style.top = c.top + 'px'; }
                } else {
                    // start area
                    token.style.left = '-40px';
                    token.style.top = (10 + i*36) + 'px';
                }
            }
            // persist current positions for next render
            try { localStorage.setItem('streamlit_positions', JSON.stringify(positions)); } catch(e){}
        }

        // If there's a lastRoll, show it briefly before animating
        if(lastRoll !== null && lastRoll !== undefined){
            const dice = document.createElement('div');
            dice.id = 'dice-overlay';
            dice.style.position = 'absolute';
            dice.style.left = '50%';
            dice.style.top = '50%';
            dice.style.transform = 'translate(-50%, -50%)';
            dice.style.width = '120px';
            dice.style.height = '120px';
            dice.style.borderRadius = '12px';
            dice.style.background = 'rgba(0,0,0,0.75)';
            dice.style.color = '#fff';
            dice.style.display = 'flex';
            dice.style.alignItems = 'center';
            dice.style.justifyContent = 'center';
            dice.style.fontSize = '48px';
            dice.style.zIndex = 9999;
            dice.textContent = String(lastRoll);
            wrapper.appendChild(dice);
            // show for 700ms then remove and animate
            setTimeout(()=>{
                if(dice && dice.parentNode) dice.parentNode.removeChild(dice);
                animateTokens();
            }, 700);
        } else {
            // no dice to show, animate quickly
            setTimeout(animateTokens, 50);
        }
    })();
    </script>
    """

    # inject JSON data
    html = html.replace('__POSITIONS__', positions_json).replace('__COLORS__', player_colors_js).replace('__LAST_ROLL__', last_roll_json)

    html += "</div>"  # close board-wrapper
    return html

# UI
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("보드 상태")
    # render HTML board with colored tokens
    board_html = render_board()
    # increase height so the last row/cell is visible
    components.html(board_html, height=640)
with col2:
    st.subheader("정보")
    st.write(f"전체 칸 수: {BOARD_SIZE}")
    if st.session_state.winner:
        st.success(f"🎉 학생 {st.session_state.winner}님이 승리했습니다!")
    else:
        st.write(f"현재 차례: 학생 {st.session_state.current_player + 1}")
    if st.session_state.last_roll is not None:
        st.write(f"마지막 주사위: {st.session_state.last_roll}")
    st.write("위치:")
    for i, pos in enumerate(st.session_state.positions):
        st.write(f"- 학생 {i+1}: {pos} 칸")

# 행동 버튼
col_roll, col_reset = st.columns(2)
with col_roll:
    if st.button("주사위 굴리기"):
        roll_dice()
with col_reset:
    if st.button("초기화"):
        reset_game()

# 히스토리
st.subheader("이동 기록")
if st.session_state.history:
    for idx, (player, roll, new_pos) in enumerate(reversed(st.session_state.history), 1):
        st.write(f"{idx}. 학생 {player} → 주사위 {roll} → 위치 {new_pos}")
else:
    st.write("아직 이동 기록이 없습니다.")
# ...existing code...