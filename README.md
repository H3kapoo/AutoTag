# AutoTagger

Simple tagging utility for python custom tests or c/c++ Unit/Module tests.

---

### Usage
Program supports tagging tests (adding a jira id or a feature id or anything else) by supplying it with with a GIT
generated diff file.

Based on that file, the program will automatically tag tests with the user supplied tags and values. The addition
of tags/values occurs before the removal step.

```bash
    #1 Make some changes inside your project test files (add/modify tests)
    #2 Generate diff file using git and redirect it into a file of choice
    $ git diff > my_diff.diff

    #3 Feed the diff file into the program along with (each optional, all options can co-exist on same line):
        #3.1 --py_put tag[val,val2] tag2[...] ... <- to put tags and values for each python test that changed based on
        #                                            the diff supplied
        $ python3 autoTagger.py my_diff.diff --py_put some_tag[some_value1, another_value]

        #3.2 --py_remove tag[val,val2] tag2[...] ... <- to remove tags and values for each python test that changed based
        #                                               on the diff supplied
        $ python3 autoTagger.py my_diff.diff --py_remove some_tag[some_value1, another_value]

        #3.3 --um_put tag[val,val2] tag2[...] ... <- to put tags and values to the top of the Unit/Module file that changed
        #                                            based on the diff supplied
        $ python3 autoTagger.py my_diff.diff --um_put some_tag[some_value1, another_value]

        #3.4 --um_remove tag[val,val2] tag2[...] ... <- to remove tags and values to the top of the Unit/Module file that
        #                                               changed based on the diff supplied
        $ python3 autoTagger.py my_diff.diff --um_remove some_tag[some_value1, another_value]
    
    #4 Done! All tests tagged as requested!

```
---

### Configuration

To maintain single-file script idea, the configuration structure is placed inside the script itself, and consists of:

*```-- General --```*

```max_row_len``` Used for row wrapping in case line gets too long
```enable_logs``` Enables/disables log printing

*```-- Python Tests Specific --```*

```ignored_markers``` List of strings denoting what markers the program shall ignore and not tokenize
```marker_to_split``` Simple string that denotes how a valid marker (in the test header) starts like
```markers_end``` Tells when the programs shall consider header lines are done processing.

*```-- UT/MT Specific --```*

```comm_start / comm_start_secondary``` String denoting how a header usually starts
```comm_end / comm_end_secondary``` String denoting how a header usually ends
```footer_hint``` If there's already a header footer (usually copyright message) inside the file header, give a hint to the program of how that looks like so it will use it instead of using ```footer_msg```
```footer_msg``` Custom message user can put at the end of the header, usually a copyright message

---
### Examples

#### Python Test File

The python tests inside the file MUST be separated by 3 new line delimiters **(\n\n\n)**, otherwise the program will not be able
to accurately separate function headers from their body.

```python
    # --- Before File ---
    # Some include headers
    ...

    @marker.base.tag('val', 'val2')
    @some_ignored_tag(...)
    def my_nice_test():
        # body...


    @some_ignored_tag(...)
    def my_nice_test_second():
        # body...
```

```bash
    # User modified test "my_nice_test", generated diff, and:
    # -- "tag" will have a new value "newValueForTag" added to it AND will have value "val2" removed
    # -- "newTag" tag will be introduced now with values "newTagValue" and "secondValue"
    # -- "my_nice_test_second" remains as is, it was not changed
    $ python3 autoTagger.py my_diff.diff --py_put tag[newValueForTag] newTag[newTagValue, secondValue] --py_remove tag[val2]
```

```python
    # --- After File ---
    # Some include headers
    ...

    @marker.base.tag('newTagValue')
    @marker.base.newTag('newTagValue', 'secondValue')
    @some_ignored_tag(...)
    def my_nice_test():
        # body...


    @some_ignored_tag(...)
    def my_nice_test_second():
        # body...
```

#### Unit/Module Test File

The Unit/Module test files (UM File) has no specific requirements, it will only add/remove tags at the top of the file, so
no per test separation needs to be performed like for python test files.

```c++
    // --- Before File ---

    /**
     * tag: value, value2
     * otherTag: value3, value4
     *
     * Some copyright line
    **/

    // Some include headers
    ...

    TEST_F(TestSuite, TestName)
    {
        // body...
    }

    // other tests
```

```bash
    # User modified UM file, generated diff, and:
    # -- "tag" will have a new value "newValueForTag" added to it AND will have value "value2" removed
    # -- "newTag" tag will be introduced now with values "newTagValue" and "secondValue"
    # -- "my_nice_test_second" remains as is, it was not changed
    $ python3 autoTagger.py my_diff.diff --um_put tag[newValueForTag] newTag[newTagValue, secondValue] --um_remove tag[value2]
```

```c++
    // --- After File ---

    /**
     * tag: value, newValueForTag
     * otherTag: value3, value4
     * newTag: newTagValue, secondValue
     *
     * Some copyright line
    **/

    // Some include headers
    ...

    TEST_F(TestSuite, TestName)
    {
        // body...
    }

    // other tests
```