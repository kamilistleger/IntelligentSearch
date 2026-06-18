"""
Student Agent for Infinite Tic-Tac-Toe

Students implement their search algorithm and can:
- Create/join lobbies to play against other students
- Challenge the AI to improve their ranking
- View leaderboards (AI and PvP)
"""

from client import GameClient
from typing import Tuple
import json
import os
import sys
import random
import time



class TimeUp(Exception):
    """Raised when we've blown our move-time budget mid-search."""
    pass


class StudentAgent:
    def __init__(self):
        self.my_symbol = None
        self.opponent_symbol = None
        self.max_moves = 20
        self.depth = 5
        self.time_budget = 0.8  # seconds, leave headroom under server limit

    def get_move(self, state):
        """Called by server - return (row, col)"""
        board = self._parse_grid(state['grid'])

        self.my_symbol = state['your_symbol']
        self.opponent_symbol = state['opponent_symbol']

        if not board:
            return (0, 0)

        win = self._find_winning_move(board, self.my_symbol)
        if win:
            return win

        block = self._find_winning_move(board, self.opponent_symbol)
        if block:
            return block

        deadline = time.time() + self.time_budget
        best_move = None

        for d in range(1, self.depth + 1):
            try:
                score, move = self.alpha_beta(
                    board, d,
                    float('-inf'), float('inf'),
                    True, deadline
                )
                if move is not None:
                    best_move = move
            except TimeUp:
                # Keep whatever the previous completed depth found
                break

        if best_move is None:
            occupied = set(board.keys())
            moves = list(self._get_adjacent_moves(occupied))
            if moves:
                best_move = random.choice(moves)
            else:
                best_move = (0, 0)

        return best_move
    

    def get_children(self, board, player):
        """Generate next states - ordered by heuristic, not random"""
        if len(board) == 0:
            new_board = {(0, 0): player}
            return [((0, 0), new_board)]

        occupied = set(board.keys())
        moves = list(self._get_adjacent_moves(occupied))

        # Sort by quick heuristic so strong moves are tried first -
        # this is what makes alpha-beta pruning actually effective
        moves.sort(
            key=lambda m: self._evaluate_position(board, m, player),
            reverse=True
        )
        moves = moves[:self.max_moves]

        children = []
        for move in moves:
            new_board = board.copy()
            new_board[move] = player
            children.append((move, new_board))

        return children

    def alpha_beta(self, board, depth, alpha, beta, is_maximizing,
                    deadline, last_move=None, last_player=None):
        """Alpha-beta pruning with deadline enforcement"""
        if time.time() > deadline:
            raise TimeUp()

        # Only check if the move that was JUST played created a win -
        # much cheaper than scanning the whole board every node
        if last_move is not None and self._is_winning_move(board, last_move, last_player):
            if last_player == self.my_symbol:
                return 100000, None
            else:
                return -100000, None

        if depth == 0:
            return self.evaluate(board), None

        if is_maximizing:
            best_score = -999999
            best_move = None

            for move, child in self.get_children(board, self.my_symbol):
                score, _ = self.alpha_beta(
                    child, depth - 1, alpha, beta, False,
                    deadline, move, self.my_symbol
                )

                if score > best_score:
                    best_score = score
                    best_move = move

                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break

            return best_score, best_move

        else:
            best_score = 999999
            best_move = None

            for move, child in self.get_children(board, self.opponent_symbol):
                score, _ = self.alpha_beta(
                    child, depth - 1, alpha, beta, True,
                    deadline, move, self.opponent_symbol
                )

                if score < best_score:
                    best_score = score
                    best_move = move

                beta = min(beta, best_score)
                if beta <= alpha:
                    break

            return best_score, best_move
        
    def evaluate(self, board):
        my_score = 0
        opponent_score = 0


        for pos in board:
            if board[pos] == self.my_symbol:
                my_score += self._piece_score(board, pos, self.my_symbol)
            elif board[pos] == self.opponent_symbol:
                opponent_score += self._piece_score(board, pos, self.opponent_symbol)

        return my_score - (opponent_score* 1.5)  # weight opponent's potential more heavily of probeer 2.0 of meer 
    

    def _piece_score(self, board, pos, player):
        row, col = pos
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        score = 0

        for dr, dc in directions:
            count = 1
            for step in range(1, 6):
                r, c = row + dr*step, col + dc*step
                if board.get((r, c)) == player:
                    count += 1
                else:
                    break
            for step in range(1, 6):
                r, c = row - dr*step, col - dc*step
                if board.get((r, c)) == player:
                    count += 1
                else:
                    break


            if count >= 6:
                score += 1000000
            elif count == 5:
                    score += 100000
            elif count == 4:
                    score += 10000
            elif count == 3:
                    score += 100
            elif count == 2:
                    score += 10    
        return score  
                


    #--------------------------------------------------------------- #

    def _parse_grid(self, grid_dict):
        """Convert grid dict to board"""
        board = {}
        for key, value in grid_dict.items():
            try:
                row, col = eval(key) if isinstance(key, str) else key
                board[(row, col)] = value
            except:
                pass
        return board
    


    #--------------------------------------------------------------- #
    
    def _parse_grid(self, grid_dict):
        """Convert grid dict to board"""
        board = {}
        for key, value in grid_dict.items():
            try:
                row, col = eval(key) if isinstance(key, str) else key
                board[(row, col)] = value
            except:
                pass
        return board
    
    def _find_winning_move(self, grid: dict, player: str) -> Tuple[int, int]:
        """Check for immediate win"""
        candidates = self._get_adjacent_moves(set(grid.keys()))
        
        for move in candidates:
            if self._is_winning_move(grid, move, player):
                return move
        return None
    
    def _is_winning_move(self, grid: dict, move: Tuple[int, int], player: str) -> bool:
        """Check if move creates 6 in a row"""
        row, col = move
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            count = 1
            for i in range(1, 6):
                if grid.get((row + dr*i, col + dc*i)) == player:
                    count += 1
                else:
                    break
            for i in range(1, 6):
                if grid.get((row - dr*i, col - dc*i)) == player:
                    count += 1
                else:
                    break
            if count >= 6:
                return True
        return False
    
    def _get_adjacent_moves(self, occupied: set) -> set:
        """Get empty positions adjacent to occupied ones"""
        candidates = set()
        for row, col in occupied:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    new_pos = (row + dr, col + dc)
                    if new_pos not in occupied:
                        candidates.add(new_pos)
        return candidates
    
    def _find_best_move(self, grid: dict) -> Tuple[int, int]:
        """Find best move - IMPROVE THIS!"""
        occupied = set(grid.keys())
        candidates = self._get_adjacent_moves(occupied)
        
        if not candidates:
            return (0, 0)
        
        # Simple: pick move that creates longest line
        best_move = None
        best_score = -1
        
        for move in candidates:
            score = self._evaluate_position(grid, move, self.my_symbol)
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move or (0, 0)
    
    def _evaluate_position(self, grid: dict, move: Tuple[int, int], player: str) -> int:
        """Evaluate position - IMPROVE THIS!"""
        row, col = move
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        max_count = 0
        
        for dr, dc in directions:
            count = 1
            for i in range(1, 6):
                if grid.get((row + dr*i, col + dc*i)) == player:
                    count += 1
                else:
                    break
            for i in range(1, 6):
                if grid.get((row - dr*i, col - dc*i)) == player:
                    count += 1
                else:
                    break
            max_count = max(max_count, count)
        
        return max_count


def main():
    """Main menu for students"""

    SERVER_URL = " https://inf-tac-toe.apps.dataintelligencelab.nl"
    CREDENTIALS_FILE = ".credentials"

    # ------------------------------------------------------------------ #
    # Credential helpers
    # ------------------------------------------------------------------ #

    def load_credentials() -> dict:
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_credentials(username: str, player_id: str, api_token: str) -> None:
        with open(CREDENTIALS_FILE, "w") as f:
            json.dump({"username": username, "player_id": player_id, "api_token": api_token}, f)
        os.chmod(CREDENTIALS_FILE, 0o600)

    # ------------------------------------------------------------------ #
    # Auth flow
    # ------------------------------------------------------------------ #

    client = GameClient(SERVER_URL)
    saved = load_credentials()

    print("=" * 60)
    print("Infinite Tic-Tac-Toe — Student Agent")
    print("=" * 60)

    if saved.get("username") and saved.get("api_token"):
        print(f"\nSaved credentials found for user '{saved['username']}'.")
        use_saved = input("Use saved credentials? [Y/n]: ").strip().lower()
        if use_saved in ("", "y", "yes"):
            client.player_id = saved["player_id"]
            client.username = saved["username"]
            client.api_token = saved["api_token"]
            print(f"✓ Using saved credentials for '{client.username}'")
        else:
            saved = {}

    if not client.api_token:
        print("\n1 = Login to existing account")
        print("2 = Register a new account")
        auth_choice = input("Choice: ").strip()
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        try:
            if auth_choice == "1":
                client.login(username, password)
            else:
                client.register(username, password)
        except Exception as exc:
            print(f"\nAuth failed: {exc}")
            sys.exit(1)
        save_credentials(client.username, client.player_id, client.api_token)
        print(f"  Credentials saved to '{CREDENTIALS_FILE}'")

    agent = StudentAgent()

    # ------------------------------------------------------------------ #
    # Main menu
    # ------------------------------------------------------------------ #

    while True:
        print("\n" + "=" * 60)
        print(f"Logged in as: {client.username}")
        print("Menu:")
        print("  1. Challenge AI (Ranked)")
        print("  2. Create Lobby (vs Player)")
        print("  3. Join Lobby (vs Player)")
        print("  4. View Leaderboards")
        print("  5. Play as Human (Web Interface)")
        print("  6. Exit")
        print("=" * 60)

        choice = input("\nChoice: ").strip()

        if choice == "1":
            print("\nChallenging AI...")
            game_id = client.challenge_ai()
            client.play_game(game_id, agent.get_move, verbose=True)

        elif choice == "2":
            print("\nCreating lobby...")
            raw = input("Max moves (default 200): ").strip()
            max_moves = int(raw) if raw else 200

            lobby_id = client.create_lobby(max_moves=max_moves)
            print(f"\nLobby ID: {lobby_id}")
            print("Share this ID with your opponent!")

            game_id = client.wait_for_lobby_start(lobby_id)
            client.play_game(game_id, agent.get_move, verbose=True)

        elif choice == "3":
            print("\nAvailable lobbies:")
            lobbies = client.list_lobbies()

            if not lobbies:
                print("No open lobbies available.")
                continue

            for i, lobby in enumerate(lobbies, 1):
                print(f"\n  {i}. Host: {lobby['host_name']}")
                print(f"     Max Moves: {lobby['max_moves']}")
                print(f"     Time Limit: {lobby['move_time_limit']}s")
                print(f"     Lobby ID: {lobby['lobby_id']}")

            lobby_num = input("\nEnter lobby number (or press Enter to enter ID): ").strip()

            if lobby_num == "":
                lobby_id = input("Enter lobby ID: ").strip()
            else:
                try:
                    lobby_id = lobbies[int(lobby_num) - 1]['lobby_id']
                except (ValueError, IndexError):
                    print("Invalid choice!")
                    continue

            game_id = client.join_lobby(lobby_id)
            client.play_game(game_id, agent.get_move, verbose=True)

        elif choice == "4":
            for table, label in (("ai", "AI Challenge"), ("pvp", "Player vs Player")):
                print(f"\n{'='*60}")
                print(f"Leaderboard — {label}")
                print(f"{'='*60}")
                try:
                    leaderboard = client.get_leaderboard(table)
                except Exception as exc:
                    print(f"  Could not fetch: {exc}")
                    continue

                if not leaderboard:
                    print("  No ranked games played yet.")
                    continue

                print(f"  {'Rank':<5} {'Player':<20} {'Score':<8} {'W–L–D':<12} {'Win%'}")
                print("  " + "-" * 55)
                for i, p in enumerate(leaderboard, 1):
                    total = p['total_games']
                    win_pct = (p['wins'] / total * 100) if total else 0.0
                    wld = f"{p['wins']}-{p['losses']}-{p['draws']}"
                    print(f"  {i:<5} {p['player_name']:<20} {p['score']:<8} {wld:<12} {win_pct:.1f}%")

            input("\nPress Enter to continue...")

        elif choice == "5":
            print("\nStarting AI challenge for the web interface...")
            game_id = client.challenge_ai()
            url = f"{SERVER_URL}/play?api_token={client.api_token}&game_id={game_id}"
            print(f"\nOpen this URL in your browser:")
            print(f"  {url}")
            input("\nPress Enter when done...")

        elif choice == "6":
            print("\nGoodbye!")
            break

        else:
            print("Invalid choice!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)