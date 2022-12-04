from core import *

def recover_graph(symbols, blocks_quantity):
    
    for symbol in symbols:
        
        neighbors, deg = generate_indexes(symbol.index, symbol.degree, blocks_quantity)
        symbol.neighbors = {x for x in neighbors}
        symbol.degree = deg

        if VERBOSE:
            symbol.log(blocks_quantity)

    return symbols

def reduce_neighbors(block_index, blocks, symbols):
    
    for other_symbol in symbols:
        if other_symbol.degree > 1 and block_index in other_symbol.neighbors:
        
            # XOR the data and remove the index from the neighbors
            other_symbol.data = np.bitwise_xor(blocks[block_index], other_symbol.data)
            other_symbol.neighbors.remove(block_index)

            other_symbol.degree -= 1
            
            if VERBOSE:
                print("XOR block_{} with symbol_{} :".format(block_index, other_symbol.index), list(other_symbol.neighbors.keys())) 


def decode(symbols, blocks_quantity):

    symbols_n = len(symbols)
    assert symbols_n > 0, "There are no symbols to decode."

    # We keep `blocks_n` notation and create the empty list
    blocks_n = blocks_quantity
    blocks = [None] * blocks_n

    # Recover the degrees and associated neighbors using the seed (the index, cf. encoding).
    symbols = recover_graph(symbols, blocks_n)
    print("Graph built back. Ready for decoding.", flush=True)
    
    solved_blocks_count = 0
    iteration_solved_count = 0
    start_time = time.time()
    
    while iteration_solved_count > 0 or solved_blocks_count == 0:
    
        iteration_solved_count = 0

        # Search for solvable symbols
        for i, symbol in enumerate(symbols):

            # Check the current degree. If it's 1 then we can recover data
            if symbol.degree == 1: 

                iteration_solved_count += 1 
                block_index = next(iter(symbol.neighbors)) 
                symbols.pop(i)

                # This symbol is redundant: another already helped decoding the same block
                if blocks[block_index] is not None:
                    continue

                blocks[block_index] = symbol.data

                if VERBOSE:
                    print("Solved block_{} with symbol_{}".format(block_index, symbol.index))
              
                # Update the count and log the processing
                solved_blocks_count += 1
                log("Decoding", solved_blocks_count, blocks_n, start_time)

                # Reduce the degrees of other symbols that contains the solved block as neighbor             
                reduce_neighbors(block_index, blocks, symbols)

    print("\n----- Solved Blocks {:2}/{:2} --".format(solved_blocks_count, blocks_n))

    return np.asarray(blocks), solved_blocks_count