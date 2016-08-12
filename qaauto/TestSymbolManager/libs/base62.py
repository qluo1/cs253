## IRESS base62 encoder

#ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

def base62_encode(num, alphabet=ALPHABET):
    """Encode a number in Base X

    `num`: The number to encode
    `alphabet`: The alphabet to use for encoding
    """
    if (num == 0):
        return alphabet[0]
    arr = []
    base = len(alphabet)
    while num:
        rem = num % base
        num = num // base
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)

def base62_decode(string, alphabet=ALPHABET):
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for encoding
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1

    return num

import sys
if __name__ == "__main__":
    """
    # print base62_encode(1)
    # print base62_encode(666666)
    print base62_decode("054mKn")
    # print base62_encode(7502079)

    print base62_decode("054ppP")
    ### PROD order test
    print base62_decode("0gsPho"),"0gsPho"

    print base62_encode(635119100), 63511910 
    print base62_encode(633574640), 63357464 
    #

    """
    if len(sys.argv) != 2:
        print "please specify argc"
        sys.exit(1)
    print sys.argv
    print base62_encode(int(sys.argv[1]))
    