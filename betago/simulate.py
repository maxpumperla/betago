def simulate_game(board, black_bot, white_bot):
    """Simulate a game between two bots."""
    move_num = 1
    whose_turn = 'b'
    moves = []
    while moves[-2:] != [None, None]:
        if whose_turn == 'b':
            next_move = black_bot.select_move('b')
            if next_move is not None:
                white_bot.apply_move('b', next_move)
        else:
            next_move = white_bot.select_move('w')
            if next_move is not None:
                black_bot.apply_move('w', next_move)
        if next_move is not None:
            board.apply_move(whose_turn, next_move)
        moves.append(next_move)
        move_num += 1
        whose_turn = 'b' if whose_turn == 'w' else 'w'
