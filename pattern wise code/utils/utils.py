import random


def format_datetime(dt):
    # Directly format the datetime object
    formatted_date = dt.strftime('%Y-%m-%d, %I:%M %p')
    return formatted_date

def get_initials(name):
    parts = str(name).split()
    if len(parts) >= 2:
        initials = parts[0][0] + parts[1][0]
    elif len(parts) == 1:
        initials = parts[0][0]
    else:
        initials = ""
    return initials.upper()



def random_color(value):
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


def get_filename(file_path):
    return file_path.split("\\")[-1]


