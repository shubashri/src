'''
Created on 20/08/2014

@author: Ismail Faizi
'''
from models import Product, Image, Pictogram, Scanning, PRODUCT_KEY, IMAGE_KEY,\
    PICTOGRAM_KEY, SCANNING_KEY
from google.appengine.ext import ndb, deferred
import logging

BATCH_SIZE = 100

def UpdateProductSchema(cursor=None, num_updated=0, has_more=True):
    if has_more:
        query = Product.query(ancestor=PRODUCT_KEY)

        to_put = []
        products, next_cursor, more = query.fetch_page(page_size=BATCH_SIZE,
                                                       start_cursor=cursor)

        for p in products:
            p.published = True
            p.scans = 0
            p.inappropriate_reports = 0
            p.wrong_product_reports = 0
            to_put.append(p)

        if to_put:
            ndb.put_multi(to_put)
            num_updated += len(to_put)
            logging.debug('Put %d product entities to Datastore for a total of %d', len(to_put), num_updated)
            UpdateProductSchema(next_cursor, num_updated, more)
        else:
            logging.debug('UpdateProductSchema completed with %d updated!', num_updated)


def UpdateImageSchema(cursor=None, num_updated=0, has_more=True):
    if has_more:
        query = Image.query(ancestor=IMAGE_KEY)

        to_put = []
        images, next_cursor, more = query.fetch_page(page_size=BATCH_SIZE,
                                                     start_cursor=cursor)

        for i in images:
            i.OCRResult = None
            to_put.append(i)

        if to_put:
            ndb.put_multi(to_put)
            num_updated += len(to_put)
            logging.debug('Put %d image entities to Datastore for a total of %d', len(to_put), num_updated)
            UpdateImageSchema(next_cursor, num_updated, more)
        else:
            logging.debug('UpdateImageSchema completed with %d updated!', num_updated)

def UpdatePictogramSchema(cursor=None, num_updated=0, has_more=True):
    if has_more:
        query = Pictogram.query(ancestor=PICTOGRAM_KEY)

        to_put = []
        pictograms, next_cursor, more = query.fetch_page(page_size=BATCH_SIZE,
                                                         start_cursor=cursor)

        for i in pictograms:
            if 'GHS06' == i.name:
                i.order = 1
                i.title = 'Skull & Crossbones'
            if 'GHS08' == i.name:
                i.order = 2
            if 'GHS07' == i.name:
                i.order = 3
            if 'GHS05' == i.name:
                i.order = 4
            if 'GHS09' == i.name:
                i.order = 5
            i.description = ''

            to_put.append(i)

        if to_put:
            ndb.put_multi(to_put)
            num_updated += len(to_put)
            logging.debug('Put %d pictogram entities to Datastore for a total of %d', len(to_put), num_updated)
            UpdatePictogramSchema(next_cursor, num_updated, more)
        else:
            logging.debug('UpdatePictogramSchema completed with %d updated!', num_updated)

def UpdateScanningSchema(cursor=None, num_updated=0, has_more=True):
    if has_more:
        query = Scanning.query(ancestor=SCANNING_KEY)

        to_put = []
        scannings, next_cursor, more = query.fetch_page(page_size=BATCH_SIZE,
                                                        start_cursor=cursor)

        for s in scannings:
            s.deleted = False
            to_put.append(s)

        if to_put:
            ndb.put_multi(to_put)
            num_updated += len(to_put)
            logging.debug('Put %d scanning entities to Datastore for a total of %d', len(to_put), num_updated)
            UpdateScanningSchema(next_cursor, num_updated, more)
        else:
            logging.debug('UpdateScanningSchema completed with %d updated!', num_updated)
