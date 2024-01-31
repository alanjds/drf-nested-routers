__author__ = 'wangyi'


def belong(left, right):
    for i in left:
        if i not in right:
            return False
    return True
