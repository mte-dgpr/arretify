#
# Copyright (c) 2025 Direction générale de la prévention des risques (DGPR).
#
# This file is part of Arrêtify.
# See https://github.com/mte-dgpr/arretify for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import unittest

from bs4 import BeautifulSoup

from arretify.utils.testing import normalized_soup

from .html_tree_navigation import closest_common_ancestor, is_descendant, is_parent


class TestIsDescendant(unittest.TestCase):

    def test_is_descendant(self):
        # Arrange
        soup = normalized_soup(
            """
            <div>
                bla <a>link</a>
                <span class="parent">
                    blo <b class="child">bold blo</b>
                </span>
            </div>
            """
        )
        parent_tag = soup.find(class_="parent")
        child_tag = soup.find(class_="child")
        assert parent_tag is not None
        assert child_tag is not None

        # Assert
        assert is_descendant(child_tag, parent_tag) is True

    def test_is_not_descendant(self):
        # Arrange
        soup = normalized_soup(
            """
            <div>
                bla <a class="other">link</a>
                <span class="parent">
                    blo <b>bold blo</b>
                </span>
            </div>
            """
        )
        parent_tag = soup.find(class_="parent")
        other_tag = soup.find(class_="other")
        assert parent_tag is not None
        assert other_tag is not None

        # Assert
        assert is_descendant(parent_tag.find("b"), parent_tag.find("a")) is False


class TestIsParent(unittest.TestCase):

    def test_is_parent(self):
        # Arrange
        soup = normalized_soup(
            """
            <div>
                bla <a>link</a>
                <span class="parent">
                    blo <b class="child">bold blo</b>
                </span>
            </div>
            """
        )
        parent_tag = soup.find(class_="parent")
        child_tag = soup.find(class_="child")
        assert parent_tag is not None
        assert child_tag is not None

        # Assert
        assert is_parent(parent_tag, child_tag) is True

    def test_is_not_parent(self):
        # Arrange
        soup = normalized_soup(
            """
            <div>
                bla <a class="other">link</a>
                <span class="parent">
                    blo <b>bold blo</b>
                </span>
            </div>
            """
        )
        parent_tag = soup.find(class_="parent")
        other_tag = soup.find(class_="other")
        assert parent_tag is not None
        assert other_tag is not None

        # Assert
        assert is_parent(other_tag, parent_tag) is False


class TestClosestCommonAncestor(unittest.TestCase):

    def test_direct_parent(self):
        # Arrange
        soup = BeautifulSoup("", "html.parser")
        tag1 = soup.new_tag("div")
        tag2 = soup.new_tag("div")
        parent = soup.new_tag("div")
        parent.append(tag1)
        parent.append(tag2)

        # Act
        result = closest_common_ancestor(tag1, tag2)

        # Assert
        assert result == parent

    def test_grandparent(self):
        # Arrange
        soup = BeautifulSoup("", "html.parser")
        tag1 = soup.new_tag("div")
        tag2 = soup.new_tag("div")
        parent1 = soup.new_tag("div")
        parent2 = soup.new_tag("div")
        parent1.append(tag1)
        parent2.append(tag2)
        grandparent = soup.new_tag("div")
        grandparent.append(parent1)
        grandparent.append(parent2)

        # Act
        result = closest_common_ancestor(tag1, tag2)

        # Assert
        assert result == grandparent
