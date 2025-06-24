An example session using [`aider`](https://aider.chat) to write ehrQL.

It ends with an attempt to write a complex rule from the Diabetes QOF definitions ([`DIABETES.md`](./DIABETES.md))

- The `aider` configuration can be seen in [`aider.sh`](./aider.sh)
- The context I provide with the prompt is in [`TESTING_EHRQL.md`](./TESTING_EHRQL.md)
- The chat session can be viewed in a nice format on the [aider website](https://aider.chat/share/?mdurl=https://raw.githubusercontent.com/sebbacon/ehrql_aider_demo/refs/heads/main/.aider.chat.history.md)

It looks like the chat log doesn't capture stderr from test failures, which is the most interesting thing, as it fixed its own errors in a loop:

Error 1:

    Error loading file 'dataset_definition.py':

    Traceback (most recent call last):
    File "/workspace/dataset_definition.py", line 101, in <module>
        mild_frailty_codelist | moderate_frailty_codelist | severe_frailty_codelist
        ~~~~~~~~~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~~~~~~~~~
    TypeError: unsupported operand type(s) for |: 'list' and 'list'

    WARNING: The `|` operator has surprising precedence rules, meaning
    you may need to add more parentheses to get the correct behaviour.

    For example, instead of writing:

        a == b | x == y

    You should write:

        (a == b) | (x == y)

    Added 23 lines of output to the chat.

Error 2:

    Error loading file 'dataset_definition.py':

    Traceback (most recent call last):
    File "/workspace/dataset_definition.py", line 104, in <module>
        clinical_events.where(clinical_events.snomedct_code.is_in(all_frailty_codelist))
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ValueError: Invalid SNOMEDCTCode: 12345

    Added 12 lines of output to the chat.
