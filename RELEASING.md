VERSION=$(toml get --toml-path pyproject.toml project.version)
TAG_VERSION=v$VERSION
git diff --exit-code && \
git tag $TAG_VERSION && \
git push origin $TAG_VERSION && \ 
echo "Pushed $TAG_VERSION"