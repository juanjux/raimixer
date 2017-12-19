# RaiMixer

## IMPORTANT

This is not finished. It needs more tests, a GUI, documentation, and more
anonymity features (like selecting different delegates for every mixer account). 

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
and accounts, it's very improbable that it could be used as solid evidence in a
trial, for example.

In case you missed the warning in the first section, please note that this is
currently a very early release and some things will improve and there could be
bugs.

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

One advantage this have over an online mixer is that you don't have the trust
the online mixer operator (that will know where the funds came from and where
they'll go). Another one is that is probably faster since the online mixers 
have to wait until they have a minimum amount of users to start the mixing
process.

To be double safe you could use RaiMix before sending to RaiShaker!

## How much time does it take?

The bottleneck is the small POW done on every transaction and the fact that, at
least on my tests, the node doesn't seem to parallelize RPC requests even if
it's configured to use several threads or receive them on different connections.
So it'll depend on the number of transactions, which in turn will depend on the
number of mixing accounts and mixing rounds configured. 

This number of transactions can't be exactly predicted because the program
randomized some things, but a typical 4-accounts, 2 rounds mixing produces about
50 transactions, which on my machine take about 5 minutes to complete.

## Installation

Currently there is no setuptools/pip boilerplate (this will come soon), you 
just download the repo and do:

```bash
pip install -r requirements.txt
```

## How to use

Note: **Python 3.6 required**.

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
--amount=800m # exact amount needed in the destination, use m for mrai or k for
krai
--initial_amount=1000m # (recommended) a higher amount to make analysis harder; excess will be returned
--dest_from_multiple # send from several mixing accounts to the destination (default: send from only one)
--num_mixers=4 # number of mixing accounts to create (default=4). Higher = slower but safer.
--num_rounds=2 # number of mixing rounds to do (default=2). Ditto.
```

Mixing accounts will be deleted at the end of the operation if everything
worked.

If the RaiBlocks node or wallet crashes during the operation (which sometimes
happens), you can use the `--clean` option to recover all amounts in all the
accounts except the one you set as `--source_acc`. Please note that this can't
make out mixing accounts from previous sessions from user-created accounts, so
if you want to keep some amount in other accounts you'll have to move the 
fund manually (or run this and then restore the funds later, `--clean` won't
delete any account.)

## Roadmap

- Read the wallet and the delegates from the RailBlock's config file.
- Select the account with a greater balance as sender account if not 
  specified.
- Python package, publish on pypi.
- Optional Qt GUI.
- Windows portable .exe file.
- Testing framework emulating the node.
- Better documentation.
- Progress bars both in text and GUI mode.

If you want to contribute a PR for any of these points you're more than welcome!

## I want to thank you!

xrb_3zq1yrhgij8ix35yf1khehzwfiz9ojjotndtqprpyymixxwxnkhn44qgqmy5
