import math

#       $$$$     $$$$
#      $$$$$$   $$$$$$
#       $$$$$$$$$$$$$
#        $$$$$$$$$$$
#         $$$$$$$$$
#           $$$$$
#            $$$
#             $

def calc_row(rows):
    return rows * math.sin(rows)

def print_heart(rows):
    cols = rows

    # Buns part    
    max_length = int(rows // 3)
    max_height = max_length

    for i in range(int((max_height * 1.4) // 3)):
        print((max_length-i)*' ', i*'♡', (max_length-i)*' ', end='')
        print()
    
    for i in range(max_height // 2)[::-1]:
        print((max_length-i)*' ', i*'♡', (max_length-i)*' ', end='')
        print()
        
    # same but reversed
        
print(print_heart(30))