.PHONY: release

release: release.zip

release.zip: FORCE
	rm -f $@
	(cd ../ && zip -u9vr ./oscillodsp/$@ \
		--exclude=oscillodsp/$@ \
		--exclude=oscillodsp/*~ \
		--exclude=oscillodsp/.*swp \
		--exclude=oscillodsp/.git \
		--exclude=oscillodsp/hostapp/*/__pycache__/* \
		--exclude=oscillodsp/hostapp/.ipynb_checkpoints/ \
		--exclude=oscillodsp/hostapp/20*.csv \
		--exclude=oscillodsp/hostapp/20*.png \
		--exclude=oscillodsp/pcsim/*.o \
		--exclude=oscillodsp/pcsim/pcsim \
		--exclude=oscillodsp/ptyname.txt \
		--exclude=oscillodsp/workspace/*/.config/* \
		--exclude=oscillodsp/workspace/*/.settings/* \
		--exclude=oscillodsp/workspace/*/Debug/* \
		--exclude=oscillodsp/workspace/*/Release/* \
		--exclude=oscillodsp/workspace/*/targetConfigs/* \
		--exclude=oscillodsp/workspace/.metadata/* \
		--exclude=oscillodsp/workspace/dvt/* \
		oscillodsp/*/.style.yapf \
		oscillodsp/.editorconfig \
		oscillodsp/.gitignore \
		oscillodsp/.python-version \
		oscillodsp/LICENSE \
		oscillodsp/Makefile \
		oscillodsp/README.md \
		oscillodsp/hostapp/*.ipynb \
		oscillodsp/hostapp/*.md \
		oscillodsp/hostapp/*.py \
		oscillodsp/hostapp/*.spec \
		oscillodsp/hostapp/.gitignore \
		oscillodsp/hostapp/Makefile \
		oscillodsp/hostapp/img/ \
		oscillodsp/hostapp/oscillodsp/ \
		oscillodsp/hostapp/requirements*.txt \
		oscillodsp/hostapp/tests/ \
		oscillodsp/pcsim/ \
		oscillodsp/protobuf/ \
		oscillodsp/tools/ \
		oscillodsp/workspace/ )

FORCE: ;
