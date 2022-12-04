from core import *
from distributions import *

def get_degrees_from(distribution_name, N, k):
    
    if distribution_name == "ideal":
        probabilities = ideal_distribution(N)
    elif distribution_name == "robust":
        probabilities = robust_distribution(N)
    else:
        probabilities = None
    
    population = list(range(0, N+1))
    return [1] + choices(population, probabilities, k=k-1)
   
def encode(blocks, drops_quantity):

    # Display statistics
    blocks_n = len(blocks)
    assert blocks_n <= drops_quantity, "Because of the unicity in the random neighbors, it is need to drop at least the same amount of blocks"

    print("Generating graph...")
    start_time = time.time()

    # Generate random indexes associated to random degrees, seeded with the symbol id
    random_degrees = get_degrees_from("robust", blocks_n, k=drops_quantity)

    print("Ready for encoding.", flush=True)

    for i in range(drops_quantity):
        
        # Get the random selection, generated precedently (for performance)
        selection_indexes, deg = generate_indexes(i, random_degrees[i], blocks_n)

        # Xor each selected array within each other gives the drop (or just take one block if there is only one selected)
        drop = blocks[selection_indexes[0]]
        for n in range(1, deg):
            drop = np.bitwise_xor(drop, blocks[selection_indexes[n]])
            # drop = drop ^ blocks[selection_indexes[n]] # according to my tests, this has the same performance

        # Create symbol, then log the process
        symbol = Symbol(index=i, degree=deg, data=drop)
        
        if VERBOSE:
            symbol.log(blocks_n)

        log("Encoding", i, drops_quantity, start_time)

        yield symbol

    print("\n----- Correctly dropped {} symbols (packet size={})".format(drops_quantity, PACKET_SIZE))
