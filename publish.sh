python bumpversion.py patch
rm dist/*
python -m build
twine upload dist/*
git commit -v -a -m "publish `date`"
git push
echo "to update installed package:"
echo "pip install --upgrade --force-reinstall hplib"
