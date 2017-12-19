# RaiMixer

## IMPORTANT

This is not finished. It needs more tests, a GUI, documentation, and more
anonimity features (like selecting different delegates for every mixer account). 

**It could also could eat your funds alive and leave you poor and homeless. 
You've been warned.**

## What is this?

This is a fund mixer/shaker to improve anonymity on
[RaiBlocks](https://raiblocks.net) transactions. It will create a (configurable)
number of mixer accounts and send the amount between them and the original
source account in a number of (configurable) mixing rounds until finally all the
funds are sent to the destination account. 

This takes
advantage of the fast and feeless transactions of the awesome [RaiBlocks
cryptocurrency](https://raiblocks.net).

## Is this safe? 

Depends on your definition of safe. This probably won't protect you from a well
done blockchain analysis from professionals. But since they can only get a
certain % of certainly, that lowers as you increase the number of mixing rounds
and accounts, it's very improbable that it could be used as evidence in a trial.

In case you missed the warning above, please note that this is currently a very
early release and some things will improve. For example it doesn't 

## Won't the nodes know where the amounts are coming because of my IP?

No, nodes doesn't have a way to know of a block they're receiving is being
originated in a peer or simply propagated.

## Is this safer than an online mixer?

Not really. The advantage of an online mixer like
[RaiShaker](https://raishaker.net/) is that it mixes amounts from different
users. So even while nodes can't know if different accounts are from the same or
different persons, an comprehensive analysis could see if all the funds from the
first transactions before mixing came from knew exchanges accounts and thus can
guess than the transactions following that one are to the mixers accounts.
RaiShaker avoids that problem mixing the funds from its users together.

To be double safe you could use this before sending to RaiShaker!

## How much time does it take?

The bottleneck seems to be the POW and the fact that, at least on my tests, the
node doesn't seem to paralelize RPC requests even if it's configured to use
several threads. So it'll depend on the number of transactions, which in turn
will depend on the number of mixing accounts and mixing rounds configured. 

This number of transactions can't be exactly predicted because the program
randomized some things, but a typical 4-accounts, 2 rounds mixing produces about
50 transactions, which on my machine take about 5 minutes to complete.

## How to use

Note: Python 3.6 required.

Edit your `~/RaiBlocks/config.json` and set to `"true"` the settings called
`enable_control` and `rpc_enable`. The close and reopen your wallet or node 
and unlock it. It must remain running while this script runs.

```bash
python raimix.py --help
```

Example:

```bash
python raimix.py --wallet=<your wallet from your config.json>
--source_acc=xrb_<acount where you have the funds>
--dest_acc=xrb_<destination account>
--amount=800k # exact amount needed in the destination
--initial_amount=100m # (recommended) a higher amount to make analysis harder; excess will be returned
--dest_from_multiple # send from several mixing accounts to the destination (default: send from only one)
--num_mixers=4 # number of mixing accounts to create (default=4). Higher = slower but safer.
--num_rounds=2 # number of mixing rounds to do (default=2). Ditto.
```

Mixing accounts will be deleted at the end of the operation if everything
worked.

If the RaiBlocks node or wallet crashes during the operation (which sometimes
happens), you can use the `--clean` option to recover all amounts in all the
accounts except the one you set as `--source_acc`. Please note that this won't 
