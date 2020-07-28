# crossword class
# crossword object creates an empty board with word bank and clues

# nee to find a file w words and their definition -> (word: definition)
import re
from pathlib import Path
import random

BLOCKCHAR = '#'
OPENCHAR = '-'
PROTECTEDCHAR = '~'


class Crossword:
    def __init__(self, vocab_file, width=8, height=8):
        """
        :param vocab_file: string
            name of file with all possible words and their definitions
        :param width: int
            width of board
        :param height: int
            height of board
        """
        self.width = width
        self.height = height
        self.board = '-' * (width * height)
        self.blockct = int(width * height / 6)
        self.used_words = dict()
        self.vocab = dict()
        path = Path(vocab_file)
        with open(path, mode="r") as opened_file:
            lines = opened_file.readlines()
        for line in lines:
            word, definition = line.split(': ')
            self.vocab[word] = definition

        empty_pos = [i for i in range(len(self.board))]
        self.board, num = self.place_blocks(self.board, 0, empty_pos)
        self.clean_protected()

    def place_blocks(self, board, curr_blockct, empty_pos):
        """
        places blockct of blocks on the board such that the board is symmetrical and no word is too short
        """
        if curr_blockct == self.blockct:  # if you have enough blocks, stop
            return board, curr_blockct
        if len(empty_pos) == 0:  # if there are no more empty spaces, stop
            return board, curr_blockct
        # empty_pos.sort(key=lambda pos: self.pick_pos_heuristic(pos), reverse=True)
        picked_pos = empty_pos[random.randint(0, len(empty_pos)-1)]
        empty_pos.remove(picked_pos)
        board = board[0:picked_pos] + BLOCKCHAR + board[picked_pos + 1:]
        new_board, curr_blockct = self.block_helper(board)  # get string with no border
        if curr_blockct > self.blockct:
            board = board[0:picked_pos] + OPENCHAR + board[picked_pos + 1:]  # if too many blocks, remove prev block
            curr_blockct = board.count(BLOCKCHAR)
        else:
            new_board, curr_blockct = self.make_palindrome(new_board)
            # pass string with no border, new_board is a string with no border
            if curr_blockct > self.blockct:
                board = board[0:picked_pos] + OPENCHAR + board[picked_pos + 1:]
                curr_blockct = board.count(BLOCKCHAR)
            else:
                bordered = self.add_border(new_board)
                c = self.area_fill(bordered, self.width + 2, bordered.find(OPENCHAR), set())
                if c != len(new_board) - new_board.count(BLOCKCHAR):
                    board = board[0:picked_pos] + OPENCHAR + board[picked_pos + 1:]
                    curr_blockct = board.count(BLOCKCHAR)
                else:
                    temp_pos = [z for z in empty_pos if new_board[z] == OPENCHAR]
                    final_board, curr_blockct = self.place_blocks(new_board, curr_blockct, temp_pos)
                    if curr_blockct == self.blockct:
                        bordered = self.add_border(final_board)
                        connected = self.area_fill(bordered, self.width + 2, bordered.find(OPENCHAR), set())
                        if connected == len(final_board) - final_board.count(BLOCKCHAR):
                            return final_board, curr_blockct
                        else:
                            board = board[0:picked_pos] + OPENCHAR + board[picked_pos + 1:]
                            curr_blockct = board.count(BLOCKCHAR)
                    else:
                        board = board[0:picked_pos] + OPENCHAR + board[picked_pos + 1:]
                        curr_blockct = board.count(BLOCKCHAR)
        empty_pos = [z for z in empty_pos if board[z] == OPENCHAR]
        return self.place_blocks(board, curr_blockct, empty_pos)

    def block_helper(self, board):
        xw = self.add_border(board)
        illegalRE = "[#](.?[A-Z~]|[A-Z~].?)[#]"
        newH = self.height + 2
        for c in range(2):
            if re.search(illegalRE, xw):
                return board, len(board)
            xw = self.transpose(xw, len(xw) // newH)
            newH = len(xw) // newH
        subRE = "[{}]{}(?=[{}])".format(BLOCKCHAR, OPENCHAR, BLOCKCHAR)
        subRE2 = "[{}]{}{}(?=[{}])".format(BLOCKCHAR, OPENCHAR, OPENCHAR, BLOCKCHAR)
        subRE3 = "[#]-([A-Z~])-(?=[#])"
        subRE4 = "[#]--([A-Z~])(?=[#])"
        subRE5 = "[#]([A-Z~])--(?=[#])"
        subRE6 = "[#]([A-Z~][A-Z~])-(?=[#])"
        subRE7 = "[#]-([A-Z~][A-Z~])(?=[#])"
        subRE8 = "[#]([A-Z~])-([A-Z~])(?=[#])"
        newH = len(xw) // (self.width + 2)
        for counter in range(2):
            xw = re.sub(subRE, BLOCKCHAR * 2, xw)
            xw = re.sub(subRE2, BLOCKCHAR * 3, xw)
            xw = re.sub(subRE3, r"#~\1~", xw)
            xw = re.sub(subRE4, r"#~~\1", xw)
            xw = re.sub(subRE5, r"#\1~~", xw)
            xw = re.sub(subRE6, r"#\1~", xw)
            xw = re.sub(subRE7, r"#~\1", xw)
            xw = re.sub(subRE8, r"#\1~\2", xw)
            xw = self.transpose(xw, len(xw) // newH)
            newH = len(xw) // newH
        newboard = self.remove_border(xw)
        return newboard, newboard.count(BLOCKCHAR)

    def make_palindrome(self, board):  # make board rotationally symmetrical
        new_board = board[::-1]
        new_board = re.sub("[A-Z]", "~", new_board)
        return self.combine(board, new_board)

    def area_fill(self, board, width, index, visited):
        if index < 0 or index >= len(board):
            return 0
        if index in visited or board[index] == BLOCKCHAR:
            return 0
        visited.add(index)
        return 1 + self.area_fill(board, width, index - 1, visited) + \
               self.area_fill(board, width, index - width, visited) + \
               self.area_fill(board, width, index + 1, visited) + \
               self.area_fill(board, width, index + width, visited)

    def add_border(self, board):  # adds border to board
        xw = BLOCKCHAR * (self.width + 3)
        xw += (BLOCKCHAR * 2).join([board[p:p + self.width] for p in range(0, len(board), self.width)])
        xw += BLOCKCHAR * (self.width + 3)
        return xw

    def remove_border(self, board):
        newboard = ''
        for r in range(self.width + 2, len(board) - (self.width + 2), self.width + 2):
            newboard += board[r + 1: self.width + r + 1]
        return newboard

    def combine(self, board, new_board):  # combines 2 boards together
        combined_board = '-' * len(board)
        for i in range(len(board)):
            a, b = board[i], new_board[i]
            if a == b:
                combined_board = combined_board[:i] + a + combined_board[i + 1:]
            elif a == OPENCHAR:
                combined_board = combined_board[:i] + b + combined_board[i + 1:]
            elif b == OPENCHAR:
                combined_board = combined_board[:i] + a + combined_board[i + 1:]
            elif ((a.isalpha() or a == PROTECTEDCHAR) and b == BLOCKCHAR) or (b == PROTECTEDCHAR and a == BLOCKCHAR):
                return board, len(board)
            elif a.isalpha() and b == PROTECTEDCHAR:
                combined_board = combined_board[:i] + a + combined_board[i + 1:]
            elif b == PROTECTEDCHAR and not a.isalpha():
                combined_board = combined_board[:i] + b + combined_board[i + 1:]
            else:
                combined_board = combined_board[:i] + a + combined_board[i + 1:]
        return combined_board, combined_board.count(BLOCKCHAR)

    def clean_protected(self):
        self.board = self.board.replace(PROTECTEDCHAR, OPENCHAR)

    def transpose(self, xw, newWidth):
        return ''.join([xw[col::newWidth] for col in range(newWidth)])

    def display_board(self):
        for i in range(self.height):
            for j in range(self.width):
                print(self.board[i * self.width + j], end=" ")
            print()

    def solve_board(self):
        """
        fill board in with words from vocab, save their positions, direction, and definition
        :return:
        """
        pass

    def get_game(self):
        """
        makes a file with the clean generated board and words/clues
        :return:
        """
        pass

    def pick_pos_heuristic(self, pos):
        pos_row, pos_col = pos // self.width, pos % self.width
        up, down, left, right = -1, -1, -1, -1
        next_block = self.board.find('#')
        while next_block > 0:
            nb_row, nb_col = next_block // self.width, next_block % self.width
            if nb_col == pos_col:
                if nb_row < pos_row:
                    up = pos_row - nb_row - 1
                else:
                    down = nb_row - pos_row - 1
            elif nb_row == pos_row:
                if nb_col > pos_col:
                    right = nb_col - pos_col - 1
                else:
                    left = pos_col - nb_col - 1
            else:
                if up == -1: up = pos_row
                if down == -1: down = self.height - pos_row - 1
                if left == -1: left = pos_col
                if right == -1: right = self.width - pos_col - 1
            next_block = self.board.find('#', next_block + 1)
        if up == -1: up = pos_row
        if down == -1: down = self.height - pos_row - 1
        if left == -1: left = pos_col
        if right == -1: right = self.width - pos_col - 1
        return left * right + up * down
