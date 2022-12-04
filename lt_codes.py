#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import math
import argparse
import tkinter
import numpy as np
import core
from encoder import encode
from decoder import decode
from tkinter import *
from tkinter import ttk
from tkinter import filedialog


if __name__ == "__main__":

    #Create an instance of Tkinter frame
    win = Tk()


    #Set the geometry of Tkinter frame
    win.geometry("750x250")

    def openInputFile():
        inputtxt.delete("1.0", "end")
        tf = filedialog.askopenfilename(
            initialdir="C:/Users/MainFrame/Desktop/",
            title="Open Text file",
            filetypes=(("Text Files", "*.txt"),)
        )
        pathh.insert(END, tf)
        tf = open(tf)  # or tf = open(tf, 'r')

        data = tf.read()
        inputtxt.insert(END, data)
        tf.close()

        file1 = open('image_restart.txt', 'w')
        # Writing a string to file
        file1.write(data)
        file1.close()

    def openOutputFile():
        outputtxt.delete("1.0", "end")

        tf = open('image_restart-copy.txt', 'r')
        data = tf.read()
        outputtxt.insert(END, data)
        tf.close()

    def clearData():
        inputtxt.delete("1.0", "end")
        outputtxt.delete("1.0", "end")
        encodetxt.delete("1.0", "end")

    def display_text():
        # global entry
        # string = entry.get()
        # print(string)
        # label.configure(text=string)

        def blocks_read(file, filesize):
            blocks_n = math.ceil(filesize / core.PACKET_SIZE)
            blocks = []

            # Read data by blocks of size core.PACKET_SIZE
            for i in range(blocks_n):

                data = bytearray(file.read(core.PACKET_SIZE))

                if not data:
                    raise "stop"

                # The last read bytes needs a right padding to be XORed in the future
                if len(data) != core.PACKET_SIZE:
                    data = data + bytearray(core.PACKET_SIZE - len(data))
                    assert i == blocks_n - \
                        1, "Packet #{} has a not handled size of {} bytes".format(
                            i, len(blocks[i]))

                # Paquets are condensed in the right array type
                blocks.append(np.frombuffer(data, dtype=core.NUMPY_TYPE))

            return blocks


        def blocks_write(blocks, file, filesize):
            """ Write the given blocks into a file
            """

            count = 0
            for data in recovered_blocks[:-1]:
                file_copy.write(data)
                count += len(data)

            # Convert back the bytearray to bytes and shrink back
            last_bytes = bytes(recovered_blocks[-1])
            shrinked_data = last_bytes[:filesize % core.PACKET_SIZE]
            file_copy.write(shrinked_data)

        def ACGT(val):
            s = ""
            if(len(val)%2 == 1):
                val = '0'+ val
            
            for i in range(0, len(val), 2):
                if val[i] == '0' and val[i+1] == '0':
                    s += 'A'
                elif val[i] == '0' and val[i+1] == '1':
                    s += 'C'
                elif val[i] == '1' and val[i+1] == '0':
                    s += 'G'
                elif val[i] == '1' and val[i+1] == '1':
                    s += 'T'            

            return s

        def ACGTtoBIN(val):
            s = ""
            for i in range(0, len(val)):
                if(val[i] == 'A'):
                    s+='00'
                elif(val[i] == 'C'):
                    s+='01'
                elif(val[i] == 'G'):
                    s+='10'
                elif(val[i] == 'T'):
                    s+='11'
            return s

        def convertToACGT(symbolData):
            ans = []
            for val in symbolData:
                ans.append(ACGT(str(bin(val)[2:])))
            return ans
        
        def convertToVAL(symbolData):
            ans = []
            for val in symbolData:
                binaryVal = ACGTtoBIN(val)
                ans.append(int(binaryVal, 2))
            return np.array(ans)


        string = "image_restart.txt"
        red = 2.0
        parser = argparse.ArgumentParser(
            description="Robust implementation of LT Codes encoding/decoding process.")
        # parser.add_argument(
        #     "filename", help="file path of the file to split in blocks")
        parser.add_argument("-r", "--redundancy",
                            help="the wanted redundancy.", default=2.0, type=float)
        parser.add_argument(
            "--systematic", help="ensure that the k first drops are exactaly the k first blocks (systematic LT Codes)", action="store_true")
        parser.add_argument(
            "--verbose", help="increase output verbosity", action="store_true")
        parser.add_argument(
            "--x86", help="avoid using np.uint64 for x86-32bits systems", action="store_true")
        args = parser.parse_args()

        core.NUMPY_TYPE = np.uint32 if args.x86 else core.NUMPY_TYPE
        core.SYSTEMATIC = True if args.systematic else core.SYSTEMATIC
        core.VERBOSE = True if args.verbose else core.VERBOSE

        with open(string, "rb") as file:

            print("Redundancy: {}".format(red))
            print("Systematic: {}".format(core.SYSTEMATIC))

            filesize = os.path.getsize(string)
            print("Filesize: {} bytes".format(filesize))

            # Splitting the file in blocks & compute drops

            file_blocks = blocks_read(file, filesize)
            file_blocks_n = len(file_blocks)
            drops_quantity = int(file_blocks_n * red)

            print("Blocks: {}".format(file_blocks_n))
            print("Drops: {}\n".format(drops_quantity))

            # Generating symbols (or drops) from the blocks
            file_symbols = []
            for curr_symbol in encode(file_blocks, drops_quantity=drops_quantity):
                file_symbols.append(curr_symbol)

            # for symbol in file_symbols:
            #     print(symbol.data)
            for symbol in file_symbols:
                symbol.data = convertToACGT(symbol.data)
                encodetxt.insert(END, symbol.data)
            
            # HERE: Simulating the loss of packets?
            
            # ######################################################################################################

            for symbol in file_symbols:
                symbol.data = convertToVAL(symbol.data)
            # Recovering the blocks from symbols

            # for symbol in file_symbols:
            #     print(symbol.data)

            recovered_blocks, recovered_n = decode(
                file_symbols, blocks_quantity=file_blocks_n)

            if core.VERBOSE:
                print(recovered_blocks)
                print("------ Blocks :  \t-----------")
                print(file_blocks)

            if recovered_n != file_blocks_n:
                print("All blocks are not recovered, we cannot proceed the file writing")
                exit()

            splitted = string.split(".")
            if len(splitted) > 1:
                filename_copy = "".join(splitted[:-1]) + "-copy." + splitted[-1]
            else:
                filename_copy = string + "-copy"

            # Write down the recovered blocks in a copy
            with open(filename_copy, "wb") as file_copy:
                blocks_write(recovered_blocks, file_copy, filesize)

            print("Wrote {} bytes in {}".format(
                os.path.getsize(filename_copy), filename_copy))


            label.configure(text="Encoding and Decoding Successfull.")
            openOutputFile()


    frame1 = Frame(win)
    frame1.pack()

    frame2 = Frame(win)        
    frame2.pack()

    frame3 = Frame(win)        
    frame3.pack()

    
# #Initialize a Label to display the User Input
    

    ilbl = Label(frame1, text="Input Data/Encoded Data", font=("Courier 10 bold"))
    ilbl.pack(side=TOP)
    inputtxt = Text(frame1, width=40, height=10)
    inputtxt.pack(pady=20, side= LEFT)
    encodetxt = Text(frame1, width=40, height=10)
    encodetxt.pack(pady=20, side=LEFT)
    
    olbl = Label(frame2, text="Output Data", font=("Courier 10 bold"))
    olbl.pack(side=TOP)
    outputtxt = Text(frame2, width=40, height=10)
    outputtxt.pack(pady=20, side=LEFT)
    #Create a Button to validate Entry Widget
    ttk.Button(frame3, text="Run", width=20, command=display_text).pack(pady=20)
    ttk.Button(frame3, text="ClearData", width=20, command=clearData).pack(pady=20)

    label = Label(win, text="Select Input File", font=("Courier 22 bold"))
    label.pack()

    pathh = Entry(win)
    pathh.pack(side=LEFT, expand=True, fill=X, padx=20)

    Button(
        win,
        text="Select File",
        command=openInputFile
    ).pack(side=RIGHT, expand=True, fill=X, padx=20)


    win.mainloop()
