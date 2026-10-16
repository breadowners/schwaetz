import pytest

from phone import private_hostname


def test_phone_hostname_is_one_exact_private_dns_name():
    assert private_hostname("My-Mac.tail123.ts.net.") == "my-mac.tail123.ts.net"
    for value in ("*", "*.ts.net", "example.com", "https://mac.tail123.ts.net",
                  "mac.tail123.ts.net:443", "mac.tail123.ts.net/notes", "127.0.0.1", "-mac.tail123.ts.net"):
        with pytest.raises(ValueError):
            private_hostname(value)
