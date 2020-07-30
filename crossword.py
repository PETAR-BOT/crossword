# crossword class
# crossword object creates an empty board with word bank and clues

# nee to find a file w words and their definition -> (word: [definitions])
# how to open all the json files in a folder and read all of them?
import re
from pathlib import Path
import random
import string
from collections import defaultdict
import pickle

BLOCKCHAR = '#'
OPENCHAR = '-'
PROTECTEDCHAR = '~'


class Crossword:
    def __init__(self, vocab_file=r'vocab.pkl', width=5, height=5):
        """
        :param vocab_file: string
            pickle file with words and meanings
        :param width: int
            width of board
        :param height: int
            height of board
        """
        self.width = width
        self.height = height
        self.board = '-' * (width * height)
        self.blockct = int(width * height / 6)
        self.vocab = defaultdict(list)
        self.load_vocab(vocab_file)

        # make board
        empty_pos = [i for i in range(len(self.board))]
        self.board, num = self.place_blocks(self.board, 0, empty_pos)
        self.clean_protected()

        # solve puzzle
        self.patterns = dict()
        self.letter_count = {letter: 0 for letter in string.ascii_uppercase}
        self.make_patterns()
        self.down, self.across = self.find_word_pos(self.board)
        self.solved_board = self.solve_board(self.board, set(), self.down, self.across)

        # show puzzle
        self.get_game()
        self.get_answers()

    def load_vocab(self, path):
        path = Path(path)
        with open(path, mode='rb') as openedfile:
            self.vocab = pickle.load(openedfile)

    def save_vocab(self, path):
        path = Path(path)
        with open(path, mode='wb') as openedfile:
            self.vocab = pickle.dump(self.vocab, openedfile)

    def place_blocks(self, board, curr_blockct, empty_pos):
        """
        places blockct of blocks on the board such that the board is symmetrical and no word is too short
        """
        if curr_blockct == self.blockct:  # if you have enough blocks, stop
            return board, curr_blockct
        if len(empty_pos) == 0:  # if there are no more empty spaces, stop
            return board, curr_blockct
        # empty_pos.sort(key=lambda pos: self.pick_pos_heuristic(pos), reverse=True)
        empty_pos.sort(key=lambda pos: self.pick_pos_heuristic(pos, board), reverse=True)
        picked_pos = empty_pos[0]
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
                c = self.check_connected(bordered, self.width + 2, bordered.find(OPENCHAR), set())
                if c != len(new_board) - new_board.count(BLOCKCHAR):
                    board = board[0:picked_pos] + OPENCHAR + board[picked_pos + 1:]
                    curr_blockct = board.count(BLOCKCHAR)
                else:
                    temp_pos = [z for z in empty_pos if new_board[z] == OPENCHAR]
                    final_board, curr_blockct = self.place_blocks(new_board, curr_blockct, temp_pos)
                    if curr_blockct == self.blockct:
                        bordered = self.add_border(final_board)
                        connected = self.check_connected(bordered, self.width + 2, bordered.find(OPENCHAR), set())
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

    def check_connected(self, board, width, index, visited):
        if index < 0 or index >= len(board):
            return 0
        if index in visited or board[index] == BLOCKCHAR:
            return 0
        visited.add(index)
        return 1 + self.check_connected(board, width, index - 1, visited) + \
               self.check_connected(board, width, index - width, visited) + \
               self.check_connected(board, width, index + 1, visited) + \
               self.check_connected(board, width, index + width, visited)

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

    def display_board(self, board):
        for i in range(self.height):
            for j in range(self.width):
                print(board[i * self.width + j], end=" ")
            print()

    def display_board_in_file(self, board, file):
        for i in range(self.height):
            for j in range(self.width):
                print(board[i * self.width + j], end=" ", file=file)
            print('\n', file=file)

    def make_patterns(self):
        for word in self.vocab:
            word = word.upper()
            key = '-' * len(word)
            if key not in self.patterns:
                self.patterns[key] = {word}
            else:
                words = self.patterns[key]
                words.add(word)
                self.patterns[key] = words
            for pos in range(len(word)):
                new_key = key[:pos] + word[pos] + key[pos + 1:]
                if new_key not in self.patterns:
                    self.patterns[new_key] = {word}
                else:
                    words = self.patterns[new_key]
                    words.add(word)
                    self.patterns[new_key] = words
                self.letter_count[word[pos]] += 1

    def find_word_pos(self, board):
        down = dict()
        across = dict()
        for pos in range(len(board)):
            if board[pos] != '#' and (pos % self.width == 0 or board[pos - 1] == '#'):
                pattern, a = board[pos], pos + 1
                while a < pos + self.width - pos % self.width and board[a] != '#':
                    pattern += board[a]
                    a += 1
                across[pos] = pattern
            if board[pos] != '#' and (pos < self.width or board[pos - self.width] == '#'):
                pattern, a = board[pos], pos + self.width
                while a < len(board) and board[a] != '#':
                    pattern += board[a]
                    a += self.width
                down[pos] = pattern
        return down, across

    def solve_board(self, board, used, down, across):
        """
        fill board in with words from vocab, save their positions, direction, and definition
        :return:
        """
        # if board is full, check that all words in board are real words (ie in the vocab)
        # if a word is not a real word, return none; if all words are real, return board
        # find position w/ pattern easiest to fill in (has the fewest possibilities, or already partially filled)
        # find words that can fit that pattern, choose the most likely to be used (common word? common letter?)
        # for every possible word, place it in the board and recur
        if '-' not in board:
            for word in down.values():
                if word not in self.vocab:
                    return None
            for word in across.values():
                if word not in self.vocab:
                    return None
            return board
        pattern, index, possible_words = self.most_constrained_pattern(down, across)
        possible_words = list(set(possible_words) - set(used))
        possible_words.sort(key=self.heuristic, reverse=True)
        for word in possible_words:
            new_board = self.add_word(board, word, index)
            new_used_words = used.copy()
            new_used_words.add(word)
            new_down, new_across = self.find_word_pos(new_board)
            if index[1] == 'D':
                words = self.new_words(across, new_across)
            else:
                words = self.new_words(down, new_down)
            bad_board = False
            for pos in words:
                pat = words[pos]
                if '-' not in pat:
                    if pat in used or pat not in self.vocab:
                        bad_board = True
                        break
                    else:
                        new_used_words.add(pat)
                else:
                    if index[1] == "A":
                        word_list = self.get_possible_words(pat, (pos % self.width + index[0] - pos) // self.width)
                    else:
                        word_list = self.get_possible_words(pat, index[0] + (pos // self.width - index[0] // self.width) * self.width - pos)
                    word_list = list(set(word_list) - set(new_used_words))
                    if len(word_list) == 0:
                        bad_board = True
                        break
            if bad_board:
                continue
            else:
                newBoard = self.solve_board(new_board, new_used_words, new_down, new_across)
                if newBoard is not None:
                    return newBoard
        return None

    def heuristic(self, word):
        val = 0
        for letter in word:
            if letter in self.letter_count:
                val += self.letter_count[letter]
        return val

    def most_constrained_pattern(self, down, across):
        words = None
        pattern, index = '', (-1, 'x')
        for pos in down:
            pat = down[pos]
            if pat.count('-') != 0:
                possible_words = self.get_possible_words(pat)
                if words is None or len(possible_words) <= len(words):
                    words = possible_words
                    pattern, index = pat, (pos, "D")
        for pos in across:
            pat = across[pos]
            if pat.count('-') != 0:
                possible_words = self.get_possible_words(pat)
                if words is None or len(possible_words) <= len(words):
                    words = possible_words
                    pattern, index = pat, (pos, "A")
        return pattern, index, words

    def get_possible_words(self, pattern, new_pos=-1):
        if pattern in self.patterns or new_pos == -1:
            return self.patterns[pattern]
        elif len(pattern.strip('-')) == 1:
            return set()
        else:
            new_pat = '-' * new_pos + pattern[new_pos] + '-' * (len(pattern) - new_pos - 1)
            if new_pat in self.patterns:
                new_words = self.patterns[new_pat]
            else:
                new_words = set()
            old_words = self.patterns[pattern[:new_pos] + '-' + pattern[new_pos + 1:]]
            possible_words = new_words & old_words
            self.patterns[pattern] = possible_words
            return possible_words

    def add_word(self, board, word, index):
        if index[1] == 'A':
            start = index[0]
            board = board[:start] + word + board[start + len(word):]
        else:
            start = index[0]
            for i in range(len(word)):
                pos = start + i * self.width
                board = board[:pos] + word[i] + board[pos + 1:]
        return board

    def new_words(self, old, new):
        words = dict()
        for key in old:
            if new[key] != old[key]:
                words[key] = new[key]
        return words

    def get_game(self):
        """
        makes a file with the clean generated board and words/clues
        :return:
        """
        f = open('crossword.txt', 'w')
        self.display_board_in_file(self.board, f)
        print("DOWN", file=f)
        self.down, self.across = self.find_word_pos(self.solved_board)
        for pos in self.down:
            print(pos, ': ', random.choice(self.vocab[self.down[pos]]), end='\n', file=f)
        print("ACROSS", file=f)
        for pos in self.across:
            print(pos, ': ', random.choice(self.vocab[self.across[pos]]), end='\n', file=f)
        print("Game ready")
        f.close()

    def get_answers(self):
        f = open('answers.txt', 'w')
        print("DOWN", file=f)
        self.down, self.across = self.find_word_pos(self.solved_board)
        for pos in self.down:
            print(pos, ': ', self.down[pos], end='\n', file=f)
        print("ACROSS", file=f)
        for pos in self.across:
            print(pos, ': ', self.across[pos], end='\n', file=f)
        f.close()

    def pick_pos_heuristic(self, pos, board):
        pos_row, pos_col = pos // self.width, pos % self.width
        up, down, left, right = -1, -1, -1, -1
        next_block = board.find('#')
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
                if down == -1: down = len(board) // self.width - pos_row - 1
                if left == -1: left = pos_col
                if right == -1: right = self.width - pos_col - 1
            next_block = board.find('#', next_block + 1)
        if up == -1: up = pos_row
        if down == -1: down = len(board) // self.width - pos_row - 1
        if left == -1: left = pos_col
        if right == -1: right = self.width - pos_col - 1
        return left * right + up * down
