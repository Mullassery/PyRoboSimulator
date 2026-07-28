class Pyrobosimulator < Formula
  desc "AI-native world simulation platform for robots and autonomous systems"
  homepage "https://github.com/Mullassery/PyRoboSimulator"
  url "https://files.pythonhosted.org/packages/pyrobosimulator-0.3.0-py3-none-any.whl"
  sha256 "5d15a3c824a952ae77ad0c2ff0f8dbc9983403d53f72041d5c39eb9e63cd73d6"
  license "MIT"

  depends_on "python@3.10"
  depends_on "python@3.11"
  depends_on "python@3.12"

  def install
    venv = virtualenv_create(libexec, "python3.11")
    venv.pip_install url
    bin.install_symlink libexec/"bin/pyrobosimulator"
  end

  test do
    system "#{bin}/pyrobosimulator", "--version"
  end
end
