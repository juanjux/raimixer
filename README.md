## IMPORTANT

This is not finished. It needs more tests, a GUI, and documentation. It could 
eat your funds alive. You've been warned.

## How to use

1. Open your config.json file, in your RaiBlocks data directory (`~/RaiBlocks`
   on Linux) and chage these values to `true`: `rpc_enable` and
   `enable_control`.

2. Run your wallet or node. Unlock it.

3. Sets your wallet and account (the wallet can be found in your `config.json`)
   in a data.json file with this format:

```json
{
    "wallet": "MYWALLETFSDFDSFKSDJFSDFSDJ",
    "orig_account": "xrb_myaccount",
    "dest_account": "xrb_dest_account"
}
```

4. Run the raimix.py script (python 3.6 required) and wait until the mixing and
   sending to the dest_account is completed.
