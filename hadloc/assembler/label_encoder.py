from hadloc.assembler.parser import write_load
from hadloc.error import CompilerException, ExceptionType
from copy import deepcopy

from hadloc.text_utils import PositionedString

# TODO As yet this cannot handle situations that are unsolvable without nop
# For example: if there is a label at instruction 255 with a single ldb instruction before it
# If we assume the ldb instruction has a length of 1, then the label will be at 255 which requires 2 instructions
# If we assume the ldb instruction has a length of 2, then the label will be at 256 which only needs a single
# instruction. In this situation a nop is required to ensure the ldb instruction is two long

"""
This file contains functions used to resolve the values of each of the labels in the assembly code. This is done by
calling encode labels, and passing in a parser object. This will rewrite the parser instructions such that there are
no longer any labels. After this stage, each instruction exactly corresponds to one machine code instruction, and all
the arguments are fully specified. 

We will call ldb instructions will a label argument unresolved load instructions. Each unresolved load instruction 
will either be assembled into 1 or 2 machine code instructions, depending on the value of the argument. Whether a 
labels length is 1 or 2, depends on which 'block' the label falls into. A block is a set of 128 instructions, 
and we label then sequentially starting at 0. If a label falls within an even block, its length will be 1, 
and if it falls within an odd block then it will have a length of 2. This means that we cannot determine the value of 
any label after load instruction with a label argument, because we don't know exactly how many instructions the load 
will assemble into before it.  To solve this we use the following algorithm: 

Each label is assigned 4 values. The first is the original location, which is the location of the label when the 
parser is originally passed in. Thus, this is the value you would get if you assume all unresolved load instructions 
assemble into 1 machine code instruction. The second and third values are the minimum and maximum possible locations 
that the label could possibly be. These are found by assuming all unresolved load instructions assemble into 1 (for 
minimum) or 2 (for maximum) machine code instructions. The final value we assign to each label is its length. This is 
the number of machine code instructions that would be required to assemble a load instruction with this label as an 
argument. We use the value of 0 if we do not currently know this value.

To begin with, we set the length of all labels to 0 (meaning it is unknown). We then call the find_lengths function, 
which will find all the length of the labels. This function starts by calling the function find_deterministic_lengths,
which finds all the lengths that are able to be found without trial and error (guessing).

The find_deterministic_lengths function uses a function called update_minmax. This determines the values of maximum and 
minimum for all labels. The find a minimum value, it assumes all unknown length labels have a length of 1, and to find 
the maximum, it assumes that all unknown length labels have a length of 2.

The find_deterministic_lengths function takes the results of the update_minmax function, and checks if any labels 
have their maximum and minimum within the same block. If they do, it sets the appropriate length for that label. We 
know that this length is correct, since we know the block that that label will be in, that regardless of the length 
of all the other labels. We then repeat this process. We update the values of minmax with the new length values, and 
check if this results in any more labels which must be within a given block. This continues until we reach a point where
we can't make anymore progress. At this point, this function finishes. Note, at each stage, we check if any labels have
their maximum equal to their minimum value. If this is the case, we mark it as finished, since it can only have one 
location.

The find_lengths function first calls find_deterministic_lengths, then finds all the remaining unknown label lengths 
through trial and error. It does this by taking the first unknown label length, assuming it is 1, and then recursively 
calling find_deterministic_lengths with this new state. It then checks if the resulting lengths are consistent with the
block they end up in. If they aren't, then the guess was wrong, so it tries a length of 2 for the first unknown label 
length, and repeats the same process. 

Once the label lengths have been found, all the load instructions with a label argument are rewritten with the 
appropriate numerical argument.
"""


def encode_labels(instructions: list[list[str | int]], labels: dict[str, int]):
    """
    Rewrites the instructions generated from the parser, such that there are no longer any labels. Any load
    instructions with a label as an argument will be replaced by equivalent assembly instructions that load the
    numerical value of the location of the label

    Args:
        instructions: The instructions generated from parsing
        labels: The labels generated from parsing
    """
    finished = {}

    label_data = {label: {'orig': labels[label], 'min': labels[label], 'max': labels[label], 'len': 0}
                  for label in labels}

    _, finished = find_lengths(label_data, finished, instructions)

    if len(finished) < len(labels):
        raise CompilerException(ExceptionType.NAME, PositionedString.empty_string(),
                                'Not able to resolve label locations')
    else:
        for i in range(len(instructions)-1, -1, -1):
            instruction = instructions[i]
            # checking that the argument is in finished is purely to filter out integer arguments. If the argument is
            # not an integer it should be in finished
            if (instruction[0] == 'ldu' or instruction[0] == 'ldb') and instruction[1] in finished:
                instructions[i:i+1] = write_load(instruction[0], finished[instruction[1]])


def find_lengths(label_data: dict[str, dict[str, int]], finished: dict[str, int], instructions: list[list[str | int]]):
    """
    Finds the 'lengths' of all the labels. The length of a label is the number of machine code instructions it takes to
    load the lower 8 bits of the label. This is achieved using a recursive algorithm of trial and error. The finished
    and labels arguments are both dictionaries where the name of the labels are the keys. The values of the labels
    dictionary are also dictionaries, containing 4 key, value pairs corresponding to the original, minimum and maximum
    locations of the label, and the length. These have the keys 'orig', 'min', 'max' and 'len' respectively. The labels
    argument contains all the labels, while the finished argument only contains the labels for which we are certain of
    the location. The values of the finished dictionary are the positions of the corresponding label in the machine
    code. Instructions is the list of instructions generated by the parser.

    Args:
        label_data: Dictionary containing the relevant information for all the labels
        finished: Dictionary containing just the labels for which we know the position
        instructions: List of instructions generated by the parser
    Returns:
        (labels, finished): The labels and finished lists. The finished list will contain all the locations of the
        labels. The return value of the labels is used for the recursion of this function, and is not needed for an
        external call to this function, since it doesn't provide any extra information beyond what the finished list
        contains
    """
    # Find all the deterministic length, which can be determined without trial and error
    find_deterministic_lengths(label_data, finished, instructions)

    # If all the labels are all already in finished, then all lengths are found, so just return the arguments
    if len(label_data) == len(finished):
        return label_data, finished

    # Otherwise, we iterate through the labels until we find the first one without a length
    # The loop will stop at this first label without a length because the body of the if statement always returns
    for label, pos in label_data.items():
        if pos['len'] == 0:
            # assume that the length is 1
            pos['len'] = 1

            # find lengths under this assumption (we must copy the arguments in case this assumption is wrong, and
            # we need to revert back to their original values)
            labels1, finished1 = find_lengths(deepcopy(label_data), deepcopy(finished), instructions)

            # boolean value determining if this assumption is consistent (i.e. if length is one, we need the eighth
            # bit to be zero)
            consistent1 = labels1[label]['min'] & 0x7F80 == labels1[label]['max'] & 0x7F80 == 0

            # Do the same, but this time assume that the length is 2
            pos['len'] = 2
            labels2, finished2 = find_lengths(deepcopy(label_data), deepcopy(finished), instructions)
            consistent2 = labels2[label]['min'] & 0x7F80 == labels2[label]['max'] & 0x7F80 == 1

            # If both assumptions are consistent, return the one that has more labels resolved.
            if consistent1 and consistent2:
                if len(finished1) < len(finished2):
                    return labels2, finished2
                return labels1, finished1

            # Otherwise, if one assumption is consistent, we return that assumption
            if consistent1:
                return labels1, finished1
            if consistent2:
                return labels2, finished2

            # Otherwise, neither assumption was consistent. This label cannot be resolved using this method, so
            # we just return the original labels
            return label_data, finished


def find_deterministic_lengths(label_data: dict[str, dict[str, int]],
                               finished: dict[str, int], instructions: list[list[str | int]]):
    """
    Finds all then lengths of the labels that are possible to be found without trial and error. Also adds any finished
    labels to the finished list. A finished label is one where we know its location for certain. See documentation for
    find_lengths for full descriptions of the arguments.

    Args:
        label_data: Dictionary containing the relevant information for all the labels
        finished: Dictionary containing just the labels for which we know the position of
        instructions: List of instructions generated by the parser
    Returns:
        (labels, finished): The labels and finished lists. The finished list will contain the labels where the position
        is known.
    """
    changed = True
    while changed:
        update_minmax(label_data, instructions)

        changed = False
        for label, pos in label_data.items():
            if pos['min'] & 0x7F80 == pos['max'] & 0x7F80 and pos['len'] == 0:
                pos['len'] = ((pos['min'] >> 7) & 0x1) + 1
                changed = True
            if pos['min'] == pos['max'] and label not in finished:
                finished[label] = pos['min']
                changed = True


def update_minmax(label_data: dict[str, dict[str, int]], instructions: list[list[str | int]]):
    """
    Finds the minimum and maximum values for each label, given the current lengths of each label. See documentation for
    find_lengths for full descriptions of the arguments.

    Args:
        label_data: Dictionary containing the relevant information for all the labels
        instructions: List of instructions generated by the parser
    """
    for label, pos in label_data.items():
        pos['min'] = pos['max'] = pos['orig']

    for i in range(len(instructions)):
        instruction = instructions[i]
        # Don't need to check ldu instructions, because labels have to fit in be 15 bits, meaning a ldu is guaranteed
        # be one instruction
        if instruction[0] == 'ldb':
            if type(instruction[1]) == str:
                if label_data[instruction[1]]['len'] == 0:
                    for label, pos in label_data.items():
                        if pos['orig'] > i:
                            pos['max'] += 1
                elif label_data[instruction[1]]['len'] == 2:
                    for label, pos in label_data.items():
                        if pos['orig'] > i:
                            pos['min'] += 1
                            pos['max'] += 1
