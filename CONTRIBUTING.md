# Contributing to IronDome

Thank you for your interest in contributing to IronDome! This guide will help you get started.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/TheKingHippopotamus/IronDome-Bunker/issues) first
2. Open a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version and OS
   - Relevant logs (ensure no sensitive data is included)

### Suggesting Features

Open an issue with the `enhancement` label. Include:
- What problem it solves
- Proposed solution
- Any alternatives you've considered

### Pull Requests

1. Fork the repository
2. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes following the guidelines below
4. Write or update tests as needed
5. Commit using [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat: add password export functionality
   fix: resolve session timeout race condition
   docs: update installation instructions
   ```
6. Push to your fork and open a PR against `main`

### Development Setup

```bash
git clone https://github.com/TheKingHippopotamus/IronDome-Bunker.git
cd IronDome-Bunker
pip install -r requirements.txt
python -m password_manager
```

### Code Guidelines

- **Python 3.8+** compatibility required
- Follow PEP 8 style conventions
- Use type hints on function signatures
- Meaningful variable and function names — no single-letter variables outside loops
- Error handling must be explicit — no silent catches
- Comments explain **why**, code explains **what**

### Security Guidelines

This is a security-critical project. All contributions must:

- **Never** log, print, or expose sensitive data (passwords, keys, salts)
- **Never** store credentials in plaintext
- **Never** weaken existing encryption or authentication mechanisms
- **Never** reduce PBKDF2 iteration counts
- Use the `secrets` module for any random generation (not `random`)
- Maintain file permission restrictions on sensitive directories
- Follow OWASP guidelines for any authentication changes

### Testing

- Every feature must include tests
- Tests go in co-located files (`*.test.py` next to the module)
- Mock external services — never hit real APIs in tests
- Never include real passwords or sensitive data in test fixtures

### What We're Looking For

- Bug fixes with clear root cause analysis
- Security improvements and hardening
- Cross-platform compatibility fixes
- Performance improvements to encryption/decryption
- Documentation improvements
- Accessibility improvements to the CLI interface

### What We Won't Merge

- Changes that weaken security
- Features that transmit data over the network
- Dependencies with known vulnerabilities
- Code without tests
- Breaking changes without migration path

## License

By contributing, you agree that your contributions will be licensed under the [GPL-3.0 License](LICENSE).

## Questions?

Open an issue or reach out to [@TheKingHippopotamus](https://github.com/TheKingHippopotamus).
