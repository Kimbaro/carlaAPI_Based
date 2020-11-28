class Stack(list):
    push = list.append  # Insert

    def is_empty(self):
        if not self:
            return True
        else:
            return False

    def peek(self):
        try:
            return self[-1]
        except IndexError:
            return None
