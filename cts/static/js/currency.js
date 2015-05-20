/* Special settings for non-US currencies. */

CURRENCIES = {
    'JOD': {
      symbol: 'JOD',
      format: "%v %s",
      precision: 3,
      thousand: ",",
      decimal: "."
    }
}

formatCurrency = function(amount, currency) {
    if (CURRENCIES[currency])
        return accounting.formatMoney(amount, CURRENCIES[currency])
    else if (currency === 'USD')
        return accounting.formatMoney(amount)  // Default.
    throw "Unknown local currency: " + currency;
}
