"""
mcts.py — Monte Carlo Tree Search
包含節點定義（Node）與主搜尋函式（mcts_best_move）。
依賴 board.py 與 rollout.py。
"""

import math
import random
import time
from board import Board, other
from rollout import rollout


# ════════════════════════════════════════════
#  強制步判斷 helpers
# ════════════════════════════════════════════

def _immediate_win(board: Board, moves: list[int], piece: str) -> int | None:
    """moves 中若有任一步能讓 piece 立即獲勝，回傳該欄位；否則回傳 None"""
    for col in moves:
        b   = board.copy()
        row = b.drop(col, piece)
        if b.check_win(col, row):
            return col
    return None


def _gives_opponent_win(board: Board, col: int, piece: str) -> bool:
    """
    AI 落子 col 之後，對手是否能立刻獲勝。
    用來過濾「送死」的步驟。
    """
    opp  = other(piece)
    b    = board.copy()
    b.drop(col, piece)
    return _immediate_win(b, b.legal_moves(), opp) is not None


# ════════════════════════════════════════════
#  MCTS 節點
# ════════════════════════════════════════════

class Node:
    """
    board   : 到達本節點時的棋盤狀態
    turn    : 從本節點出發，輪到誰落子
    parent  : 父節點（root 的 parent 為 None）
    move    : 父節點執行哪一欄落子而到達本節點
    wins    : 「走到本節點那一步的人」的累計分數
              即 parent.turn 的分數，供父節點 UCB1 選子使用
    visits  : 本節點被訪問的總次數
    untried : 尚未展開的合法落子欄位（root 層可傳入篩選後的候選清單）
    """
    __slots__ = ('board', 'turn', 'parent', 'move',
                 'children', 'visits', 'wins', 'untried')

    def __init__(self, board: Board, turn: str,
                 parent: 'Node | None' = None,
                 move:   int  | None   = None,
                 moves:  list[int] | None = None):   # None = 使用全部合法步
        self.board    = board
        self.turn     = turn
        self.parent   = parent
        self.move     = move
        self.children : list['Node'] = []
        self.visits   = 0
        self.wins     = 0.0
        self.untried  = moves if moves is not None else board.legal_moves()

    # ── UCB1 ─────────────────────────────────

    def ucb1(self, C: float = math.sqrt(2)) -> float:
        """
        wins/visits       ← 利用（選勝率高的子節點）
        C × √(ln(N)/n)   ← 探索（選訪問少的子節點）
        """
        if self.visits == 0:
            return float('inf')
        exploitation = self.wins / self.visits
        exploration  = C * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration

    def best_child(self) -> 'Node':
        return max(self.children, key=lambda c: c.ucb1())

    def is_fully_expanded(self) -> bool:
        return len(self.untried) == 0

    # ── Expansion ────────────────────────────

    def expand(self) -> 'Node':
        """隨機選一個未嘗試的落子，展開為子節點"""
        col   = self.untried.pop(random.randrange(len(self.untried)))
        nb    = self.board.copy()
        nb.drop(col, self.turn)
        child = Node(nb, other(self.turn), parent=self, move=col)
        self.children.append(child)
        return child

    # ── Backpropagation ──────────────────────

    def backpropagate(self, result: float, ai_piece: str):
        """
        result : 1.0 = AI 贏 / 0.5 = 平 / 0.0 = AI 輸

        wins 紀錄的是走到本節點那一手的人（= parent.turn）的分數，
        讓父節點在 UCB1 選子時挑對自己最有利的走法。
        """
        self.visits += 1
        if self.parent is not None:
            mover = self.parent.turn
            self.wins += result if mover == ai_piece else 1.0 - result
            self.parent.backpropagate(result, ai_piece)


# ════════════════════════════════════════════
#  MCTS 主搜尋
# ════════════════════════════════════════════

def _is_terminal(board: Board) -> bool:
    """棋盤滿了就視為終局（勝負由主迴圈在落子後判定）"""
    return board.is_full()


def mcts_best_move(board: Board, ai_piece: str,
                   time_limit: float = 2.0) -> int:
    """
    執行 MCTS 搜尋，印出各欄位勝率後回傳最佳欄位。

    進入模擬迴圈前，先做三道強制步檢查：
    ① AI 能立即獲勝         → 直接回傳，跳過模擬
    ② 對手能立即獲勝        → 直接擋住，跳過模擬
    ③ 過濾「落子後對手能立即獲勝」的步驟（送死步）

    模擬後，再做一次最終確認：
    ④ 若 MCTS 選出的步仍是送死步（候選全部送死時才會發生），
       改選送死步中模擬次數最多的（已是不得不的選擇）。
    """
    opp   = other(ai_piece)
    legal = board.legal_moves()

    # ── ① AI 能立即獲勝 ───────────────────────
    win_col = _immediate_win(board, legal, ai_piece)
    if win_col is not None:
        print(f"\n  ┌─ AI 強制步：直接獲勝")
        print(f"  └  選擇欄位 {win_col}")
        return win_col

    # ── ② 阻止對手立即獲勝 ────────────────────
    block_col = _immediate_win(board, legal, opp)
    if block_col is not None:
        print(f"\n  ┌─ AI 強制步：阻止對手獲勝")
        print(f"  └  選擇欄位 {block_col}")
        return block_col

    # ── ③ 過濾送死步，決定 MCTS 候選欄位 ──────
    safe  = [c for c in legal if not _gives_opponent_win(board, c, ai_piece)]
    # 若所有步都是送死步，只能硬著頭皮選（無解局面）
    candidates = safe if safe else legal
    forced_all_losing = len(safe) == 0

    # ── MCTS 模擬迴圈（只在候選欄位中展開 root）──
    root     = Node(board.copy(), ai_piece, moves=list(candidates))
    deadline = time.time() + time_limit
    iters    = 0

    while time.time() < deadline:
        node = root

        # Selection
        while node.is_fully_expanded() and not _is_terminal(node.board):
            node = node.best_child()

        # Expansion
        if not _is_terminal(node.board) and not node.is_fully_expanded():
            node = node.expand()

        # Simulation
        result = rollout(node.board, node.turn, ai_piece)

        # Backpropagation
        node.backpropagate(result, ai_piece)
        iters += 1

    # ── ④ 最終確認：選訪問數最多的子節點 ────────
    best = max(root.children, key=lambda c: c.visits)

    _print_analysis(root, iters, safe_moves=safe,
                    forced_all_losing=forced_all_losing,
                    chosen=best)

    return best.move


# ════════════════════════════════════════════
#  勝率分析列印
# ════════════════════════════════════════════

def _print_analysis(root: Node, iters: int,
                    safe_moves: list[int],
                    forced_all_losing: bool,
                    chosen: Node):
    """印出每個候選欄位的模擬次數與勝率，並標注送死步狀態"""

    if forced_all_losing:
        print(f"\n  ┌─ AI 分析（共 {iters} 次模擬）⚠ 所有步均送死，選最佳死法")
    else:
        print(f"\n  ┌─ AI 分析（共 {iters} 次模擬）")

    children_by_col = sorted(root.children, key=lambda c: c.move)

    for child in children_by_col:
        win_rate = child.wins / child.visits if child.visits else 0.0
        bar_len  = int(win_rate * 20)
        bar      = '█' * bar_len + '░' * (20 - bar_len)
        rate_str = f'{win_rate * 100:5.1f}%'

        # 標注
        is_chosen  = (child is chosen)
        is_losing  = (child.move not in safe_moves) and (not forced_all_losing)
        tag  = ' ← 選擇' if is_chosen  else ''
        warn = ' ⚠ 送死' if is_losing  else ''

        print(f"  │  欄 {child.move}  [{bar}] {rate_str}"
              f"  ({child.visits:5d} 次){tag}{warn}")

    print(f"  └{'─' * 47}")