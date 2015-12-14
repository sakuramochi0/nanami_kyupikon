import os
import base64
from PIL import Image

def draw_signature(infile, size_limit):
    '''画像にななみちゃんのサインを描いて、その画像を保存したファイル名を返す'''

    # load images
    sign = Image.open('nanami-millcolle-signature.png')
    im = Image.open(infile)

    # calculate sign size
    ratio_against_image = 3/5
    sign_resize_ratio = min(im.size) * ratio_against_image / sign.size[0]
    
    # resize signature
    resized_sign = sign.resize((int(sign.size[0] * sign_resize_ratio), int(sign.size[1] * sign_resize_ratio)), Image.BICUBIC)
    
    # determine paste position
    box_position = (im.size[0] // 30, im.size[1] - resized_sign.size[1])
    box = box_position + (resized_sign.size[0] + box_position[0], resized_sign.size[1] + box_position[1])

    # paste sign
    im.paste(resized_sign, box, resized_sign)

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
