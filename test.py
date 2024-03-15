import math

def print_heart(rows):
    for i in range(rows):
        for j in range(rows + 1):
            # Calculate the distance to the center of the heart
            distance_to_center = math.sqrt((i - rows)**2 + (j - rows)**2)
            # Determine if the current position is within the bounds of the heart shape
            if distance_to_center < rows + 0.5:
                print('$', end='')
            else:
                print(' ', end='')
        print()

print_heart(50)
