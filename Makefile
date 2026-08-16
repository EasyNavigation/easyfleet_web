# Minimal makefile for Sphinx documentation
#

ifeq ($(VERBOSE),1)
  Q =
else
  Q = @
endif

# You can set these variables from the command line.
SPHINXOPTS    ?=
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = "EasyFleet Documentation"
SOURCEDIR     = .
BUILDDIR      = _build

DOC_TAG      ?= development
RELEASE      ?= latest
PUBLISHDIR    = /tmp/EasyFleet

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo ""
	@echo "make publish"
	@echo "   publish generated html to easyfleet.github.io:"
	@echo "   specify RELEASE=name to publish as a tagged release version"
	@echo "   and placed in a version subfolder. Requires repo merge permission."

.PHONY: help Makefile

html:
	$(Q)$(SPHINXBUILD) -t $(DOC_TAG) -b html -d $(BUILDDIR)/doctrees $(SOURCEDIR) $(BUILDDIR)/html $(SPHINXOPTS) $(O)

clean:
	rm -fr $(BUILDDIR)

# Copy material over to the GitHub pages staging repo along with a README

publish:
	rm -rf $(PUBLISHDIR)
	git clone --reference . https://github.com/EasyNavigation/easyfleet.github.io.git $(PUBLISHDIR)
	cd $(PUBLISHDIR) && \
	git checkout gh-pages && \
	rm -fr $(PUBLISHDIR)/*
	cp -r $(BUILDDIR)/html/* $(PUBLISHDIR)
	cp scripts/.nojekyll $(PUBLISHDIR)/.nojekyll
	cd $(PUBLISHDIR) && \
	git add -A && \
	git diff-index --quiet HEAD || \
	(git commit -s -m "[skip ci] publish $(RELEASE)" && git push origin)
	rm -rf $(PUBLISHDIR)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option. $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
