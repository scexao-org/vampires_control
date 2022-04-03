

class VAMPIRES:
    """
    VAMPIRES state structure.

    This class acts as middleware between the top-level VAMPIRES commands (e.g., `vampires_beamsplitter`) and the serial or library commands. As middleware, it performs logging, updating of a local JSON state file, and updating of the SCExAO redis database.
    """

    def __init__(self):
        pass