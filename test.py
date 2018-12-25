

class Amalgalma:
    """This is example docstring"""

    def test_func(self,a):
        pass


class ClassB(Amalgalma):

    def test_func(self,a):
        mdict = locals() 
        del mdict['self'] 
        del mdict['__class__'] 
        super(ClassB, self).test_func(**locals())


    class TrololoClass:
        pass
