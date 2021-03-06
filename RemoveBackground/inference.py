import os, shutil
import sys
import argparse
import numpy as np
from PIL import Image, ExifTags
import cv2
import timeit

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as transforms

from src.models.modnet import MODNet

def combined_display(image, matte):
    # calculate display resolution
    w, h = image.width, image.height
  
    # obtain predicted foreground
    image = np.asarray(image)
    if len(image.shape) == 2:
        image = image[:, :, None]
    if image.shape[2] == 1:
        image = np.repeat(image, 3, axis=2)
    elif image.shape[2] == 4:
        image = image[:, :, 0:3]
    matte = np.repeat(np.asarray(matte)[:, :, None], 3, axis=2) / 255
    foreground = image * matte + np.full(image.shape, 255) * (1 - matte)
    foreground = Image.fromarray(np.uint8(foreground)).resize((w, h))
    return foreground
  

def convertCvToPil(image):
    color_converted = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
    pil_image = Image.fromarray(color_converted)
    return pil_image

def convertPilToCv(image):
    numpy_img = np.array(image)
    openCv_image = cv2.cvtColor(numpy_img, cv2.COLOR_RGB2BGRA)
    return openCv_image

def readImage(path):
    try:
        im = Image.open(path)
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation]=='Orientation':
                break
        exif = im._getexif()
        if exif[orientation] == 3:
            im=im.rotate(180, expand=True)
        elif exif[orientation] == 6:
            im=im.rotate(270, expand=True)
        elif exif[orientation] == 8:
            im=im.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError, TypeError):
        # cases: image don't have getexif
        pass
    return im

def geturl(im_names):
    # define cmd arguments
    # start = timeit.default_timer()
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-i', dest='input_path', type=str, help='path of input images')
    # args = parser.parse_args()
    # # check input arguments
    # im_names = args.input_path
    if not os.path.exists(im_names):
        print('Cannot find input path: {0}'.format(im_names))
        exit()

    output_folder = 'output'
    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

    ref_size = 512

    # define image to tensor transform
    im_transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ]
    )

    pretrained_ckpt = './pretrained/modnet_photographic_portrait_matting.ckpt'
    # create MODNet and load the pre-trained ckpt
    modnet = MODNet(backbone_pretrained=False)
    modnet = nn.DataParallel(modnet)

    GPU = True if torch.cuda.device_count() > 0 else False
    if GPU:
        print('Use GPU...')
        modnet = modnet.cuda()
        modnet.load_state_dict(torch.load(pretrained_ckpt))
    else:
        print('Use CPU...')
        modnet.load_state_dict(torch.load(pretrained_ckpt, map_location=torch.device('cpu')))

    modnet.eval()

    #print('Process image: {0}'.format(im_names))

    # read image & background
    im = readImage(im_names)
    
    # save a copy for image
    image = im 

    # unify image channels to 3
    im = np.asarray(im)
    if len(im.shape) == 2:
        im = im[:, :, None]
    if im.shape[2] == 1:
        im = np.repeat(im, 3, axis=2)
    elif im.shape[2] == 4:
        im = im[:, :, 0:3]

    # convert image to PyTorch tensor
    im = Image.fromarray(im)
    im = im_transform(im)

    # add mini-batch dim
    im = im[None, :, :, :]

    # resize image for input
    im_b, im_c, im_h, im_w = im.shape
    if max(im_h, im_w) < ref_size or min(im_h, im_w) > ref_size:
        if im_w >= im_h:
            im_rh = ref_size
            im_rw = int(im_w / im_h * ref_size)
        elif im_w < im_h:
            im_rw = ref_size
            im_rh = int(im_h / im_w * ref_size)
    else:
        im_rh = im_h
        im_rw = im_w
    
    im_rw = im_rw - im_rw % 32
    im_rh = im_rh - im_rh % 32
    im = F.interpolate(im, size=(im_rh, im_rw), mode='area')

    # inference
    if GPU:
        _, _, matte = modnet(im.cuda(), True)
    else:
        _, _, matte = modnet(im, True)
    # resize and save matte
    matte = F.interpolate(matte, size=(im_h, im_w), mode='area')
    matte = matte[0][0].data.cpu().numpy()

    # fix thick white edges: 
    matte = (matte*255).astype('int32')
    rows, columns = matte.shape
    sub = 100
    matte_tf = matte < 200
    matte[matte_tf] = matte[matte_tf] - sub
    matte_tf = matte < 0
    matte[matte_tf] = 0
    matte = matte.astype('uint8')
    matte = cv2.GaussianBlur(matte,(3,3),0,0)

    matte_name = im_names.split('.')[0] + '.png'
    name_image = matte_name.split('/')[-1]
    name = name_image.split('.')[0]
    res_folder = 'final_results'
    output_folder = 'output'
    output_save_matte = os.path.join(output_folder, name_image)
    Image.fromarray(matte, mode='L').save(output_save_matte, compress_level=1)
    matte = Image.open(output_save_matte)
    im = (combined_display(image, matte))
    path_result = os.path.join(res_folder, name_image)

    alpha_channel = cv2.imread(output_save_matte, -1)

    #im = cv2.imread(path_result)
    im = convertPilToCv(im)
    b_channel, g_channel, r_channel, al_channel = cv2.split(im)
    # Image 4 channel FOREGROUND img_BGRA
    img_BGRA = cv2.merge((b_channel, g_channel, r_channel, alpha_channel))

    frontImage = convertCvToPil(img_BGRA)

    # Convert image to RGBA
    frontImage = frontImage.convert("RGBA")
    
    # Save this image
    frontImage.save(os.path.join(res_folder, name +'.png'), compress_level=1)
    # print('It takes {} seconds'.format(stop - start))
    return {
        'url': path_result
        }
