# Install

Veil Alpha currently ships one public binary release:

- Linux x86_64 tarball: `veil-alpha1-linux-x86_64.tar.gz`

Download the tarball and checksum from [GitHub Releases](https://github.com/u61d/Veil/releases).

## Verify the download

Keep the tarball and checksum file in the same directory, then run:

```bash
sha256sum -c veil-alpha1-linux-x86_64.tar.gz.sha256
```

You should see `OK`.

## Extract and run

```bash
tar -xzf veil-alpha1-linux-x86_64.tar.gz
cd veil-alpha1-linux-x86_64
./run-veil.sh
```

The packaged launcher uses its own default profile path so it does not reuse an existing Firefox profile.

## Next

- Read [Linux](linux.md) for desktop entry and handler setup.
- Read [Known limitations](known-limitations.md) before treating the current Alpha as more than a measured technical preview.
