import random
import aiohttp
import asyncio
from mnemonic import Mnemonic
from bip32utils import BIP32Key
from tronpy.keys import PrivateKey
from telegram import Update
from telegram.ext import Application, CommandHandler
import logging

# Enable logging for your bot
logging.basicConfig(level=logging.INFO)

# Telegram bot token
TOKEN = '7766913521:AAG_y7Os_VxzqrIvCKEZr4kwfWXGk6PQ1OE'  # Replace with your bot's token

# Mnemonic setup
mnemo = Mnemonic("english")
seedlist = ["abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract", "absurd",
            "abuse", "access", "accident", "account", "accuse", "achieve", "acid", "acoustic",
            "acquire", "across", "act", "action", "actor", "actress", "actual", "adapt", "add",
            "addict", "address", "adjust", "admit"]

count = 0  # Address counter

# Function to generate a valid mnemonic
def generate_valid_mnemonic():
    while True:
        phrase = random.sample(seedlist, 12)
        phrase_str = ' '.join(phrase)
        if mnemo.check(phrase_str):
            return phrase_str

# Derive TRX address from mnemonic
def mnemonic_to_trx_address(mnemonic):
    seed = mnemo.to_seed(mnemonic)
    bip32_root_key = BIP32Key.fromEntropy(seed)
    bip32_child_key = bip32_root_key.ChildKey(44 + 0x80000000)  # BIP44 path for TRX (coin type 195)
    bip32_child_key = bip32_child_key.ChildKey(0).ChildKey(0)  # Account 0, external chain
    private_key = bip32_child_key.PrivateKey()

    priv_key = PrivateKey(private_key)
    return priv_key.address.base58

# Asynchronous function to check TRX balance using TronScan API
async def check_trx_balance_async(session, address):
    url = f"https://apilist.tronscan.org/api/account?address={address}"
    try:
        async with session.get(url) as response:
            data = await response.json()
            if "balance" in data:
                return int(data["balance"]) / 10**6  # Convert SUN (TRX smallest unit) to TRX
            return 0
    except Exception:
        return 0

# Find addresses with balances
async def find_crypto_with_balance(update: Update, context):
    global count
    message = await update.message.reply_text(
        "✨ Awesome! Starting a scan on TRX wallets... 🌍\n"
        "🌱 Seed: .......\n"
        "🏦 Address: .......\n"
        "🔄 Scanned wallets: 0"
    )

    async with aiohttp.ClientSession() as session:
        while True:
            # Generate mnemonic and derive addresses
            mnemonic = generate_valid_mnemonic()
            trx_address = mnemonic_to_trx_address(mnemonic)

            # Check balance concurrently
            trx_balance = await check_trx_balance_async(session, trx_address)

            count += 1

            # Update progress message every 1000 checks
            if count % 1000 == 0:
                msg = f"🔄 Scanned wallets: {count}\n"
                msg += f"🌱Seed: {mnemonic}\n"
                msg += f"🏦TRX Address: {trx_address} | Balance: {trx_balance} TRX\n"
                await message.edit_text(msg)

            # Send a separate message if balance is found
            if trx_balance > 0:
                found_message = f"🎉 Found balance!\nMnemonic: {mnemonic}\n"
                found_message += f"TRX Address: {trx_address} | Balance: {trx_balance} TRX\n"
                found_message += f"Checked Addresses: {count}"
                await update.message.reply_text(found_message)

# Start command handler
async def start(update: Update, context):
    await update.message.reply_text("Searching for TRX addresses with balance...")
    await find_crypto_with_balance(update, context)

# Set up the Application and dispatcher
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == '__main__':
    main()