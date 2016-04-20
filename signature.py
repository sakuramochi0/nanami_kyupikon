import os
import re
import base64
from PIL import Image

def draw_signature(infile, position, size_limit):
    '''画像にななみちゃんのサインを描いて、その画像を保存したファイル名を返す'''

    # load images
    sign = Image.open('nanami-millcolle-signature.png')
    im = Image.open(infile)

    # calculate sign size
    ratio_against_image = 3/5
    sign_resize_ratio = min(im.size) * ratio_against_image / sign.size[0]
    
    # resize signature
    sign = sign.resize((int(sign.size[0] * sign_resize_ratio), int(sign.size[1] * sign_resize_ratio)), Image.BICUBIC)
    
    # determine paste position
    center_x, center_y = im.size[0] // 2, im.size[1] // 2
    left = im.size[0] // 30
    right = im.size[0] - im.size[0] // 30
    top = im.size[1] // 30
    bottom = im.size[1] - im.size[1] // 30
    
    if position == 'top-left':
        box_left = left
        box_top = top
    elif position == 'top':
        box_left = center_x - sign.size[0] // 2
        box_top = top
    elif position == 'top-right':
        box_left = right - sign.size[0]
        box_top = top
    elif position == 'left':
        box_left = left
        box_top = center_y - sign.size[1] // 2
    elif position == 'center':
        box_left = center_x - sign.size[0] // 2
        box_top = center_y - sign.size[1] // 2
    elif position == 'right':
        box_left = right - sign.size[0]
        box_top = center_y - sign.size[1] // 2
    elif position == 'bottom-left':
        box_left = left
        box_top = bottom - sign.size[1]
    elif position == 'bottom':
        box_left = center_x - sign.size[0] // 2
        box_top = bottom - sign.size[1]
    elif position == 'bottom-right':
        box_left = right - sign.size[0]
        box_top = bottom - sign.size[1]
    
    box = (box_left, box_top, box_left + sign.size[0], box_top + sign.size[1])

    # paste sign
    im.paste(sign, box, sign)

    # check size limit
    while True:
        encoded_size = len(base64.encodebytes(im.tobytes()))
        if encoded_size < size_limit:
            break

        # if the size exceeded the limit, resize the image 5%
        new_size = ((int(im.size[0] * .95)), int(im.size[1] * .95))
        im = im.resize(new_size, resample=Image.LANCZOS)

    # save image
    f, _ = os.path.splitext(infile)
    outfile = os.path.join(f + '_nanami_signed.png')
    try:
        im.save(outfile)
    except IOError:
        print('Can\'t write the image:', e)
        
    return outfile

def parse_signature_position(text):
    '''textにもとづいてsignatureを配置するpositionを表す文字列を返す'''

    # find positional strings
    match = re.search(r'(?:(上|下)|(右|左)|(中央|真ん中)|.)+', text.replace('\n', ''))
    if match:
        vertical, horizon, center = match.groups()

    # convert name into english
    if horizon:
        horizon = horizon.replace('左', 'left').replace('右', 'right')
    if vertical:
        vertical = vertical.replace('上', 'top').replace('下', 'bottom')

    # determine position name
    if vertical and horizon:
        position = vertical + '-' + horizon
    elif vertical:
        position = vertical
    elif horizon:
        position = horizon
    elif center:
        position = 'center'
    else: # default
        position = 'bottom-left'
    
    return position
