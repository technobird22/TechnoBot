'''Format messages for both input and output of the model'''


def format_continued_message(raw_output_message):
    '''Format a message continuation prediction'''
    output_message = raw_output_message.splitlines()[0]

    end_loc = output_message.find(" [END]")

    if end_loc != -1:
        output_message = output_message[:end_loc]
    else:
        print("WARNING: [BAD END ERROR]")
        # output_message = "[BAD END ERROR] " + output_message

    output_message = output_message.replace(" [BR] ", '\n')

    return output_message


def format_raw_message(raw_output_message):
    '''Format a given raw message to get predicted reply'''
    DEBUG = False
    output_convo = raw_output_message.splitlines()

    for output_message in output_convo:
        if output_message.find("$: ") != -1:
            start_loc = output_message.find("$: ") + 3
            output_message = output_message[start_loc:]
            break
    else:
        print("WARNING: [BAD MATCH ERROR]")
        # output_message = "[BAD MATCH ERROR] " + output_message

    end_loc = output_message.find(" [END]")
    if end_loc != -1:
        output_message = output_message[:end_loc]
    else:
        print("WARNING: [BAD END ERROR]")
        # output_message = "[BAD END ERROR] " + output_message

    output_message = output_message.replace(" [BR] ", '\n')

    return output_message

    if DEBUG:
        print('='*30 + " Debug info: " + '='*30)
        print("---[No debug info on atm.]---")

        print('='*30 + " RAW: " + '='*30)
        print(raw_output_message)

        print('='*30 + " Formatted: " + '='*30)
        print(output_message)

def format_raw_message_convo(raw_output_message):
    '''Format a given raw message to get predicted reply'''
    DEBUG = False
    
    # if raw_output_message.find("$: ") != -1:
    #     start_loc = output_message.find("$: ") + 3
    #     output_message = raw_output_message[start_loc:]
    # else:
    #     print("WARNING: [BAD MATCH ERROR]")

    output_message = raw_output_message

    output_message = output_message.replace(" [END]", "\n" + '-' * 10)

    output_message = output_message.replace(" [BR] ", '\n')

    return output_message

    if DEBUG:
        print('='*30 + " Debug info: " + '='*30)
        print("---[No debug info on atm.]---")

        print('='*30 + " RAW: " + '='*30)
        print(raw_output_message)

        print('='*30 + " Formatted: " + '='*30)
        print(output_message)

def get_raw_message(raw_output_message):
    '''Get the raw message reply'''
    output_convo = raw_output_message.splitlines()

    for output_message in output_convo:
        if output_message.find("$: ") != -1:
            start_loc = output_message.find("\n") + 1
            output_message = output_message[start_loc:]
            break
    else:
        print("WARNING: [BAD MATCH ERROR]")
        # output_message = "[BAD MATCH ERROR] " + output_message

    end_loc = output_message.find(" [END]")

    if end_loc != -1:
        output_message = output_message[:end_loc + 14]
    else:
        print("WARNING: [BAD END ERROR]")

    return output_message

def encode_continuation(cur_input):
    '''Format/encode a message in the format for the model to autocomplete'''
    return "general $: " + cur_input


def encode_parsed_message(cur_input):
    '''Format/encode a message in the format for the model to reply to'''
    # return "general $: " + cur_input.replace('\n', ' [BR] ').replace(' bot', ' alan') + " [END]\n"
    return "computers-and-programming $: " + cur_input.replace('\n', ' [BR] ').replace(' bot', ' alan') + " [END]\n"


if __name__ == '__main__':
    RAW_MSG = "computers-and-programming $: i saw one such book just out the front [BR] indeed [END]"
    # print(get_raw_message(RAW_MSG))
    print(format_raw_message(RAW_MSG))
